# Cyber evidence lab

Could a treasury batch balance exactly while paying the wrong address? Start with the [six-row investigation](treasury-review/README.md), then replay a [public Ethereum receipt](treasury-review/public-case/README.md) containing seven USDC transfers from one sender. Both run offline with the Python 3.11 standard library. The public archive also includes a live receipt verifier.

| Project | Investigation |
| --- | --- |
| [FeedWatch](feedwatch/README.md) | Reconstruct what the SOC knew at 09:12, then explain why later arrivals change the incident scope. |
| [ExitGraph](exitgraph/README.md) | Replay a proposed offboarding change, trace the surviving grant and identify who would lose access. |
| [Treasury Review](treasury-review/README.md) | Find a wrong recipient in a balanced ERC-20 settlement batch and trace each finding to the input logs. |

Run the portfolio checks from this directory.

```powershell
python -B -m unittest -v test_cases
python -B -m unittest discover -s treasury-review -v
```
