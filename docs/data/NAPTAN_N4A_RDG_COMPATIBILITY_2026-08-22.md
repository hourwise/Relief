# NaPTAN N4A — RDG compatibility note

The model is source-neutral. NaPTAN StopAreas/StopPoints are one publisher graph; a later RDG station graph can use the same snapshot/place/node/membership pattern without treating NaPTAN as canonical transport truth.

When RDG access is available, a governed reconciliation may use a verified RDG station identifier as strong evidence, NaPTAN rail StopArea identity as a secondary key where supported, and names, modes, hierarchy, and geometry as bounded secondary evidence. A multimodal NaPTAN parent may contain a rail StopArea that corresponds to one RDG station; the parent must not be assumed to be the RDG station. Direct equivalence remains unresolved until RDG supplies its own identifiers/cross-references.

N4A therefore stores no invented RDG fields and no direct RDG↔NaPTAN key. Future source graphs can independently attach to a later reconciliation judgement without rewriting NaPTAN publisher facts.
