# Test Report

Tested with Python [[EDIT: your version]], model llama3.2:3b. All emails are synthetic.

## Manual tests (browser)

| # | Case | Input | Expected | Actual |
|---|------|-------|----------|--------|
| 1 | Clearly suspicious | Sender `PayPal Support <help@secure-login.xyz>`, subject `Urgent: account suspended`, body `Dear customer, verify your password immediately at http://192.168.1.5/login` | Rule score 60. Category High or Critical | |
| 2 | Likely legitimate | Sender `Ravi <ravi@gmail.com>`, subject `Meeting tomorrow`, body `Hi, the meeting is at 3pm tomorrow.` | Rule score 0. Category Low | |
| 3 | Ambiguous | Sender `Ravi <ravi@gmail.com>`, subject `Please verify your account`, body `Hi, please verify your account by Friday.` | Rule score 20. Category Low or Medium | |
| 4 | Malformed sender | Sender `not an email`, subject `Hello`, body `Hello there` | Accepted without crashing. Category Low | |
| 5 | Oversized body | Paste a very long text into the body box | Box stops accepting text at 10,000 characters | |
| 6 | Ollama off | Quit Ollama from the system tray, reload the page, submit case 1 | Yellow warning on the form. Result uses rules only (score 60, High) | |

## Automated tests (pytest)

| Case | Test | Expected |
|------|------|----------|
| Ollama unavailable | `test_ollama_unavailable_raises_clear_error`, `test_full_flow_when_ollama_is_down` | Clear error and rules-only score |
| Invalid model output | `test_invalid_json_is_rejected`, `test_unknown_verdict_is_rejected` | Output rejected |
| Database failure | `test_result_still_shows_when_saving_fails`, `test_history_page_survives_database_failure` | Page still works with a warning |
| Oversized input | `test_oversized_body_is_rejected`, `test_body_exactly_at_the_limit_is_accepted` | 10,001 characters rejected, 10,000 accepted |

Full pytest output: see `pytest_output.txt`. Result: [[EDIT: NN]] passed.