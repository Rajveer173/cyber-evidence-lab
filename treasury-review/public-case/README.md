# Ethereum mainnet receipt replay

This archive contains all 13 logs from one successful transaction in block 26,496,968. Seven USDC transfers share one sender. The exercise register was derived from those seven events to provide a reproducible positive control. It describes observed payments and makes no claim about the sender's identity, internal approvals or security posture.

From the treasury-review directory, run the offline reconciliation and optionally cross-check the archive with a mainnet node of your choice.

```shell
python review.py public-case/case.json public-case/logs.json
python verify_receipt.py --rpc https://ethereum-rpc.publicnode.com
```

The verifier checks the chain ID, receipt status, block hash at the receipt height and the node's finalized height. It compares the ordered log identities, emitters, topics, data and removal flags. These checks depend on the node's view of Ethereum. For an independent comparison, supply another provider.

The raw logs were retrieved through Ethereum PublicNode. [Inspect the original transaction](https://etherscan.io/tx/0x368b0297d646c3ac640bd96593f4ad5293dc1a2a3e0ea6f17a86b59c07a98425).
