# Source provenance and licensing

The top-level MIT license applies to EvoRationale implementation code and new
export tooling. It preserves the original 2026 EvoRationale Authors notice and
completes the standard MIT disclaimer. The supplied historical license file is
preserved verbatim at `archive/release_time_docs/v49/LICENSE.original`.
Historical code-release ZIPs in this export are English adaptations;
`docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json` identifies their original/adapted hashes
and changed members. The adaptation does not alter production runtime code,
captured research data, Gold reference or measured results. Historical package
checksum files describe their dated source snapshots; the current export
manifest identifies the adapted package bytes.

Third-party repository evidence is not relicensed as EvoRationale code:

| Source | Included material | Upstream information |
|---|---|---|
| Kubernetes enhancements, KEP 1287 | Captured design/history resources under `data/github/`, fixed inference inputs under `data/inputs/`, and the pinned README under `data/baseline_context/` | [Repository](https://github.com/kubernetes/enhancements); Apache-2.0 license fetched at the pinned baseline commit; exact upstream text in `LICENSES/Kubernetes-Enhancements-Apache-2.0.txt` |
| Microsoft Azure Enterprise-Scale | Uploaded Azure examples under `data/examples/azure/` and historical documentation/output resources | [Repository](https://github.com/Azure/Enterprise-Scale); current upstream [MIT license](https://github.com/Azure/Enterprise-Scale/blob/main/LICENSE); exact upstream text in `LICENSES/Azure-Enterprise-Scale-MIT.txt` |

The baseline README is identified by Git commit
`5950905de89aab2be202d28b823701276cbefea0`, Git blob
`ce5124cf7975a7d4ce6a122b2cb4006b4bc0ea2d`, and SHA-256
`f42855e662d154268b3fca59ef816128f8b7e5359e56466a174a375a930b26fa`.
Every captured artifact retains its recorded repository/source URL and version
identity. Upstream license bytes and Git blob IDs are recorded in
`docs/upstream_license_verification.json`. This later check resolves the initial
Azure license lookup gap recorded in the source audit. License metadata
does not independently authenticate every historical capture or contributor.

Historical manuscript PDFs, reference annotations and reviewer declarations
remain attributed research material. Their inclusion does not certify claims,
reviewer identity, an independent held-out test, or upstream endorsement.
Available Excel resources under `data/excel/` retain their original workbook
bytes. Their annotation or confirmation text is a recorded resource, not
independent authentication of its authors. `data/RESOURCE_INDEX.json` records
the available resource paths and identities. The scoring reference is kept
separately under `data/references/frozen_reference/`.
