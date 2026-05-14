# IPFS Concepts

## Content Addressing

Traditional hosting resolves a domain to a server location. IPFS resolves a content identifier to bytes. The identifier changes when the bytes change, which makes integrity verification part of the addressing model.

## CID

A CID is a content identifier. It contains information about the codec, multihash, and hash digest for the content. Two identical files produce the same CID; changed content produces a new CID.

## Pinning

Pinning tells an IPFS node or pinning service to keep content instead of letting garbage collection remove it. Pinning improves persistence because the content remains available from at least one provider.

## Gateway

An IPFS gateway exposes IPFS content over HTTP. It lets regular browsers fetch content with URLs such as `/ipfs/<cid>`.
