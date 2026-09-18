# Differential Syntax Validation Summary -- post-fix-2-with-fresh

## Combined
- total: 239
- agreement classes: {'inconclusive': 109, 'agree_accept': 99, 'false_positive': 8, 'agree_reject': 22, 'false_negative': 1}
- validator status: {'unknown': 8, 'validated': 110, 'partial': 12, 'invalid': 109}
- real GAUSS outcome: {'accepted': 91, 'runtime_error': 125, 'rejected_syntax_or_parse': 23}
- **FALSE NEGATIVES (1)**: ['D-007']
- **FALSE POSITIVES (8)**: ['B-025', 'B-050', 'B-051', 'B-054', 'B-062', 'C-023', 'D-013', 'D-020']

## Origin: docs_valid
- total: 50
- agreement classes: {'inconclusive': 13, 'agree_accept': 37}
- validator status: {'unknown': 4, 'validated': 38, 'partial': 8}
- real GAUSS outcome: {'accepted': 41, 'runtime_error': 9}

## Origin: model_output_fresh
- total: 25
- agreement classes: {'agree_accept': 16, 'inconclusive': 6, 'false_negative': 1, 'false_positive': 2}
- validator status: {'validated': 19, 'unknown': 2, 'invalid': 4}
- real GAUSS outcome: {'accepted': 14, 'runtime_error': 10, 'rejected_syntax_or_parse': 1}
- **FALSE NEGATIVES (1)**: ['D-007']
- **FALSE POSITIVES (2)**: ['D-013', 'D-020']

## Origin: model_output_historical
- total: 29
- agreement classes: {'agree_accept': 21, 'inconclusive': 6, 'false_positive': 1, 'agree_reject': 1}
- validator status: {'validated': 26, 'invalid': 3}
- real GAUSS outcome: {'accepted': 17, 'runtime_error': 11, 'rejected_syntax_or_parse': 1}
- **FALSE POSITIVES (1)**: ['C-023']

## Origin: mutation
- total: 135
- agreement classes: {'inconclusive': 84, 'agree_accept': 25, 'false_positive': 5, 'agree_reject': 21}
- validator status: {'invalid': 102, 'validated': 27, 'unknown': 2, 'partial': 4}
- real GAUSS outcome: {'runtime_error': 95, 'accepted': 19, 'rejected_syntax_or_parse': 21}
- **FALSE POSITIVES (5)**: ['B-025', 'B-050', 'B-051', 'B-054', 'B-062']
