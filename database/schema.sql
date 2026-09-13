CREATE DATABASE IF NOT EXISTS innerself_mbti
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE innerself_mbti;

CREATE TABLE IF NOT EXISTS test_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  public_id CHAR(36) NOT NULL,
  questionnaire_version VARCHAR(64) NOT NULL,
  mbti_result CHAR(4) NULL,
  questionnaire_result CHAR(4) NULL,
  age TINYINT UNSIGNED NULL,
  gender VARCHAR(20) NULL,
  reason_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  neutral_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  consent_language_research TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_test_sessions_public_id (public_id),
  KEY idx_test_sessions_created_at (created_at),
  KEY idx_test_sessions_mbti_result (mbti_result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS answers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id BIGINT UNSIGNED NOT NULL,
  question_id SMALLINT UNSIGNED NOT NULL,
  choice_value VARCHAR(16) NOT NULL,
  reason_raw TEXT NOT NULL,
  reason_normalized TEXT NOT NULL,
  predicted_function ENUM('Te','Ti','Fe','Fi','Ne','Ni','Se','Si') NULL,
  predicted_stance ENUM('support','oppose','mixed','unknown') NOT NULL DEFAULT 'unknown',
  raw_model_score DECIMAL(8,6) NOT NULL DEFAULT 0,
  model_status VARCHAR(40) NULL,
  token_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  has_slang TINYINT(1) NOT NULL DEFAULT 0,
  has_code_mix TINYINT(1) NOT NULL DEFAULT 0,
  has_negation TINYINT(1) NOT NULL DEFAULT 0,
  has_situational_language TINYINT(1) NOT NULL DEFAULT 0,
  language_features_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_answers_session_question (session_id, question_id),
  KEY idx_answers_predicted_function (predicted_function),
  KEY idx_answers_has_slang (has_slang),
  KEY idx_answers_has_code_mix (has_code_mix),
  KEY idx_answers_created_at (created_at),
  CONSTRAINT fk_answers_session FOREIGN KEY (session_id)
    REFERENCES test_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS function_scores (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id BIGINT UNSIGNED NOT NULL,
  te_questionnaire DECIMAL(6,2) NOT NULL, te_final DECIMAL(6,2) NOT NULL,
  ti_questionnaire DECIMAL(6,2) NOT NULL, ti_final DECIMAL(6,2) NOT NULL,
  fe_questionnaire DECIMAL(6,2) NOT NULL, fe_final DECIMAL(6,2) NOT NULL,
  fi_questionnaire DECIMAL(6,2) NOT NULL, fi_final DECIMAL(6,2) NOT NULL,
  ne_questionnaire DECIMAL(6,2) NOT NULL, ne_final DECIMAL(6,2) NOT NULL,
  ni_questionnaire DECIMAL(6,2) NOT NULL, ni_final DECIMAL(6,2) NOT NULL,
  se_questionnaire DECIMAL(6,2) NOT NULL, se_final DECIMAL(6,2) NOT NULL,
  si_questionnaire DECIMAL(6,2) NOT NULL, si_final DECIMAL(6,2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_function_scores_session (session_id),
  CONSTRAINT fk_function_scores_session FOREIGN KEY (session_id)
    REFERENCES test_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS feedback (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id BIGINT UNSIGNED NOT NULL,
  answer_id BIGINT UNSIGNED NULL,
  user_agrees TINYINT(1) NOT NULL,
  corrected_function ENUM('Te','Ti','Fe','Fi','Ne','Ni','Se','Si') NULL,
  comment VARCHAR(1000) NULL,
  reviewed_for_training TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_feedback_reviewed (reviewed_for_training),
  KEY idx_feedback_created_at (created_at),
  CONSTRAINT fk_feedback_session FOREIGN KEY (session_id)
    REFERENCES test_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_feedback_answer FOREIGN KEY (answer_id)
    REFERENCES answers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW language_training_candidates AS
SELECT
  a.id AS answer_id,
  ts.public_id AS session_public_id,
  a.question_id,
  a.reason_raw,
  a.reason_normalized,
  a.predicted_function,
  a.predicted_stance,
  a.raw_model_score,
  a.token_count,
  a.has_slang,
  a.has_code_mix,
  a.has_negation,
  a.has_situational_language,
  f.user_agrees,
  f.corrected_function,
  f.reviewed_for_training,
  a.created_at
FROM answers a
JOIN test_sessions ts ON ts.id = a.session_id
LEFT JOIN feedback f ON f.answer_id = a.id
WHERE ts.consent_language_research = 1
  AND CHAR_LENGTH(TRIM(a.reason_raw)) > 0;
