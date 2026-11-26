# Treasury Review

A treasury batch balances to the last token unit. Did the approved recipients get paid?

This offline Python 3.11 investigation matches a payment register to Ethereum ERC-20 Transfer logs by transaction, token contract and recipient. It handles split settlements and keeps the exact integer amounts. Every input log gets a numbered disposition in the report.

## Run the case

From this folder, run

```powershell
python review.py case.json logs.json
python -B -m unittest -v test_review
```

The [saved report](report.json) contains the findings, source row numbers, filtering decisions and SHA-256 fingerprints of both inputs. Row numbers are one-based positions in the logs array. Re-running the same inputs reproduces the report. A changed fingerprint identifies changed input bytes. Preserve a trusted copy of the fingerprints separately for later comparison.

## Investigator's handoff

For a second case using actual on-chain data, replay the [archived Ethereum receipt](public-case/README.md). Its seven-payment register provides a positive control for the decoder.

The supplied synthetic register authorizes PAY-81 and PAY-82 for 5,000,000 base units each in one transaction. The selected logs also total 10,000,000. Rows 1 and 2 settle PAY-81 in two parts. Row 3 sends the other 5,000,000 to the address ending in eeee. PAY-82 names the address ending in dddd. Row 4 repeats a delivery, row 5 refers to another block hash at the same height, and row 6 originates from an untracked contract.

Keep PAY-82 open. Ask the payment owner for the original approved address and any signed amendment. Independently retrieve the block and receipt before escalating the apparent payee discrepancy. A missing log in a partial export can also produce an unobserved payment.

## Demonstrate your reasoning

Show the balanced totals first. Ask which control would detect a payment to the wrong recipient. Walk through row 5 and explain why its apparent payment to the expected recipient was excluded. In a copy of the export, replace row 3's recipient topic with row 5's recipient topic. Replay it and inspect both settled tickets. The automated test exercises this counterfactual.

## Evidence and scope

Supply the result array from eth_getLogs and a case manifest in the example format. Assemble one chain per case, using an independently sourced chain ID and canonical block hashes for the reviewed heights. Obtain finalized block references from a trusted provider when the review requires finality. The tool trusts this manifest and reports its chain label. It cannot authenticate an export, prove chain finality or establish log completeness. The fixture uses invented addresses and block hashes.

The manifest joins internal ticket IDs to known settlement transaction hashes. The register must come from a trusted payment process. Approvals, native ETH, NFTs, and accounting for unusual token behavior fall outside the review. The decoder uses the standard indexed sender and recipient and the uint256 data field. [ERC-20 specification](https://eips.ethereum.org/EIPS/eip-20) · [Ethereum JSON-RPC reference](https://ethereum.org/developers/docs/apis/json-rpc/)
