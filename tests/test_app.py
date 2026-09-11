"""Regression tests; no real API keys or external AI requests are used."""
import contextlib
import io
import itertools
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app, calculate_cognitive_functions
from questions import QUESTIONS, QUESTIONNAIRE_VERSION


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def payload(self, target=None):
        return {
            'version': QUESTIONNAIRE_VERSION,
            'answers': [{'id': q['id'], 'score': (3 if q['agree_letter'] in target else -3) if target else 0, 'reason': ''} for q in QUESTIONS],
        }

    def test_pages_and_local_assets_work_from_another_working_directory(self):
        old = Path.cwd()
        try:
            os.chdir(old.parent)
            for route in ('/', '/index.html', '/result.html', '/questions', '/static/styles.css', '/static/test.js', '/static/result.js', '/static/icons.svg'):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, route)
        finally:
            os.chdir(old)

    def test_neutral_is_unresolved_and_never_forced_to_infp(self):
        response = self.client.post('/submit', json=self.payload())
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['final_result'], 'XXXX')
        self.assertEqual(result['neutral_percentage'], 100)
        self.assertEqual(result['function_stack'], [])
        self.assertEqual(result['cognitive_scores'], {})
        self.assertEqual(len(result['candidate_types']), 16)
        self.assertEqual(set(result['dimension_percentages'].values()), {50})

    def test_all_sixteen_types_with_canonical_reverse_worded_items(self):
        for letters in itertools.product('EI', 'SN', 'TF', 'JP'):
            target = ''.join(letters)
            with self.subTest(target=target):
                result = self.client.post('/submit', json=self.payload(target)).json()
                self.assertEqual(result['final_result'], target)
                self.assertEqual(len(result['function_stack']), 4)
                self.assertEqual(result['candidate_types'], [target])
                self.assertEqual(result['preference_clarity'], 100)

    def test_all_agree_is_balanced_due_to_reverse_wording(self):
        payload = self.payload()
        for item in payload['answers']:
            item['score'] = 3
        self.assertEqual(self.client.post('/submit', json=payload).json()['final_result'], 'XXXX')

    def test_one_tied_dimension_keeps_only_compatible_candidates(self):
        payload = self.payload('INTJ')
        for item in payload['answers'][:8]:
            item['score'] = 0
        result = self.client.post('/submit', json=payload).json()
        self.assertEqual(result['final_result'], 'XNTJ')
        self.assertEqual(set(result['candidate_types']), {'ENTJ', 'INTJ'})

    def test_invalid_or_duplicate_answers_are_rejected(self):
        for change in ('missing', 'duplicate', 'unknown', 'out_of_range', 'string_score', 'bool_score', 'oversized_reason', 'old_version'):
            with self.subTest(change=change):
                payload = self.payload()
                if change == 'missing': payload['answers'].pop()
                if change == 'duplicate': payload['answers'][0]['id'] = 2
                if change == 'unknown': payload['answers'][0]['id'] = 999
                if change == 'out_of_range': payload['answers'][0]['score'] = 4
                if change == 'string_score': payload['answers'][0]['score'] = '3'
                if change == 'bool_score': payload['answers'][0]['score'] = True
                if change == 'oversized_reason': payload['answers'][0]['reason'] = 'a' * 601
                if change == 'old_version': payload['version'] = 'old'
                self.assertEqual(self.client.post('/submit', json=payload).status_code, 422)

    def test_client_cannot_spoof_question_dimension_or_direction(self):
        payload = self.payload('ENTJ')
        for item in payload['answers']:
            item.update(dimension='JP', agree_letter='F', topic='forged', choice_text='forged')
        self.assertEqual(self.client.post('/submit', json=payload).json()['final_result'], 'ENTJ')

    def test_profile_validation(self):
        for age in (0, 12, 101, -1, 15.2, True):
            payload = self.payload(); payload['user_age'] = age
            self.assertEqual(self.client.post('/submit', json=payload).status_code, 422)
        for age in (None, 13, 100):
            payload = self.payload(); payload['user_age'] = age
            self.assertEqual(self.client.post('/submit', json=payload).status_code, 200)

    def test_no_ai_request_without_opt_in(self):
        with patch('psychologist.analyze_with_ai') as analyze:
            self.client.post('/submit', json=self.payload())
            analyze.assert_not_called()

    def test_missing_api_key_still_returns_complete_basic_result(self):
        payload = self.payload('INTJ'); payload['use_ai'] = True
        with patch.dict(os.environ, {}, clear=True), patch('dotenv.load_dotenv'):
            response = self.client.post('/submit', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ai_status'], 'not_configured')
        self.assertEqual(response.json()['final_result'], 'INTJ')
        self.assertTrue(response.json()['ai_note'])

    def test_ai_failure_does_not_expose_tracebacks_or_break_test(self):
        payload = self.payload('ENFP'); payload['use_ai'] = True
        with patch('psychologist.analyze_with_ai', side_effect=RuntimeError('private upstream detail')):
            response = self.client.post('/submit', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ai_status'], 'unavailable')
        self.assertNotIn('private upstream detail', response.text)
        self.assertNotIn('traceback', response.text)

    def test_cognitive_sensing_adjustment_has_correct_sign(self):
        balanced = dict.fromkeys('EISNTFJP', 12)
        sensing = {**balanced, 'S': 24, 'N': 0}
        base, _ = calculate_cognitive_functions('INTJ', balanced)
        changed, _ = calculate_cognitive_functions('INTJ', sensing)
        self.assertGreater(changed['Se'], base['Se'])
        self.assertLess(changed['Ni'], base['Ni'])

    def test_famous_people_missing_assets_use_initials(self):
        data = self.client.get('/famous_people.json').json()
        self.assertTrue(data['INTJ'])
        for people in data.values():
            for person in people:
                if person['image']:
                    self.assertEqual(self.client.get(person['image']).status_code, 200)

    def test_secret_files_not_served_and_large_payload_rejected(self):
        for path in ('/.env', '/psychologist.py', '/static/../.env'):
            self.assertEqual(self.client.get(path).status_code, 404)
        response = self.client.post('/submit', content=b'x' * 65537, headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 413)
        self.assertIn("script-src 'self'", self.client.get('/').headers['content-security-policy'])

    def test_gemini_success_and_malformed_response_fallback(self):
        from psychologist import analyze_with_ai
        for valid in (True, False):
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-placeholder'}, clear=True), patch('dotenv.load_dotenv'), patch('psychologist._dataset_context', return_value=(0.12, '')), patch('google.genai.Client') as client:
                model = client.return_value.__enter__.return_value.models
                model.generate_content.return_value.text = '{"analysis_note": "Jawabanmu menggambarkan preferensi yang bisa menjadi bahan refleksi sehari-hari."}' if valid else 'not json'
                result = analyze_with_ai('INTJ', [])
                self.assertEqual(result['ai_status'], 'available' if valid else 'unavailable')
                self.assertEqual(client.call_args.kwargs['api_key'], 'test-placeholder')

    def test_gemini_503_automatically_switches_model(self):
        from psychologist import analyze_with_ai

        class BusyError(Exception):
            code = 503

        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test-placeholder',
            'GEMINI_MODEL': 'busy-model',
            'GEMINI_FALLBACK_MODELS': 'fallback-model',
        }, clear=True), patch('dotenv.load_dotenv'), patch(
            'psychologist._dataset_context', return_value=(None, '')
        ), patch('psychologist.time.sleep'), patch('google.genai.Client') as client:
            model = client.return_value.__enter__.return_value.models
            success = type('Response', (), {
                'text': '{"analysis_note": "Fallback berhasil menyusun ulasan refleksi yang cukup panjang untuk ditampilkan."}'
            })()
            model.generate_content.side_effect = [BusyError('high demand'), success]
            result = analyze_with_ai('INTJ', [])

        self.assertEqual(result['ai_status'], 'available')
        self.assertEqual(model.generate_content.call_count, 2)
        self.assertEqual(
            [call.kwargs['model'] for call in model.generate_content.call_args_list],
            ['busy-model', 'fallback-model'],
        )


if __name__ == '__main__':
    unittest.main()
