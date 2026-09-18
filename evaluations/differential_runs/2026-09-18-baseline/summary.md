# Differential Syntax Validation Summary -- baseline

## Combined
- total: 214
- agreement classes: {'inconclusive': 104, 'agree_accept': 77, 'false_positive': 12, 'agree_reject': 16, 'false_negative': 5}
- validator status: {'unknown': 6, 'validated': 90, 'partial': 13, 'invalid': 105}
- real GAUSS outcome: {'accepted': 77, 'runtime_error': 115, 'rejected_syntax_or_parse': 22}
- **FALSE NEGATIVES (5)**: ['B-057', 'B-058', 'B-059', 'B-061', 'B-063']
- **FALSE POSITIVES (12)**: ['B-025', 'B-050', 'B-051', 'B-054', 'B-065', 'B-066', 'B-067', 'B-068', 'B-069', 'B-070', 'B-071', 'C-023']

## Origin: docs_valid
- total: 50
- agreement classes: {'inconclusive': 13, 'agree_accept': 37}
- validator status: {'unknown': 4, 'validated': 38, 'partial': 8}
- real GAUSS outcome: {'accepted': 41, 'runtime_error': 9}

## Origin: model_output_historical
- total: 29
- agreement classes: {'agree_accept': 21, 'inconclusive': 6, 'false_positive': 1, 'agree_reject': 1}
- validator status: {'validated': 26, 'invalid': 3}
- real GAUSS outcome: {'accepted': 17, 'runtime_error': 11, 'rejected_syntax_or_parse': 1}
- **FALSE POSITIVES (1)**: ['C-023']

## Origin: mutation
- total: 135
- agreement classes: {'inconclusive': 85, 'agree_accept': 19, 'false_positive': 11, 'agree_reject': 15, 'false_negative': 5}
- validator status: {'invalid': 102, 'validated': 26, 'unknown': 2, 'partial': 5}
- real GAUSS outcome: {'runtime_error': 95, 'accepted': 19, 'rejected_syntax_or_parse': 21}
- **FALSE NEGATIVES (5)**: ['B-057', 'B-058', 'B-059', 'B-061', 'B-063']
- **FALSE POSITIVES (11)**: ['B-025', 'B-050', 'B-051', 'B-054', 'B-065', 'B-066', 'B-067', 'B-068', 'B-069', 'B-070', 'B-071']
