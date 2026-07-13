# Network census scaling and optimisation

## Purpose

This report examines the performance of:

```text
rice count networks --max-rlc N
```

It describes the current algorithm, relates its running time to the number of
raw assignments, predicts the cost at `--max-rlc 9` and `10`, and proposes
optimisations. It also considers replacing exhaustive assignment enumeration
with incremental generation of canonical networks.

The figures in this report apply to the current simple primitive bundle model
and the `local-sp` network relation. They are not counts modulo rational
immittance equivalence.

## Executive summary

The present implementation is dominated by processing raw assignments. For
`--max-rlc 8`, it processes 3,657,404 assignments in about 670 seconds. The
larger measured runs cost approximately 153 to 184 microseconds per raw
assignment.

The relevant-support counts for nine and ten edges make it possible to compute
the next raw-assignment totals exactly:

| `max-rlc` | Raw assignments | Estimated current running time |
|---:|---:|---:|
| 9 | 39,430,084 | about 1 hour 41 minutes to 2 hours 1 minute |
| 10 | 450,941,128 | about 19 hours 10 minutes to 23 hours 3 minutes |

These are extrapolations. Per-assignment canonicalisation may become more
expensive with support size, so a practical allowance would be two to three
hours for `9` and at least a day for `10`.

The first optimisation should not change the mathematical enumeration. It
should change how each support is processed:

1. Validate and analyse a terminal-relevant support once, not once per
   assignment.
2. Compile its series/parallel reduction and canonical relabelling work into a
   reusable evaluation plan.
3. Enumerate one representative of each bundle assignment orbit under the
   support automorphism group.
4. Process different supports in separate worker processes.
5. Reuse the support analysis when producing diagnostics rather than running
   additional support censuses.

A reasonable engineering target is a 10- to 40-fold overall improvement at
`--max-rlc 10`, reducing an estimated day to roughly 35 minutes to 2.3 hours.
This is a target range, not a benchmark result. Profiling and prototypes are
needed before making a stronger claim.

Direct growth of canonical network states could ultimately do better. At
`--max-rlc 8`, there are only 302,102 final reduced networks for 3,657,404 raw
assignments, a ratio of about 12.1 to one. A generator whose work stayed near
the number of distinct states could therefore avoid much of the present work.
It is feasible to investigate, but completeness, resource accounting and
canonical augmentation require careful proofs. A simple mutation tree plus a
visited set is not by itself enough to guarantee an improvement.

## Present counting model

### Supports and bundle assignments

The source objects are connected, loopless, simple, unlabelled support graphs.
For each graph, the implementation:

1. finds unordered terminal-pair orbits under graph automorphisms;
2. rejects a terminal pair unless every support edge lies on a simple path
   between the terminals; and
3. assigns one simple primitive bundle to each support edge.

There are seven non-empty simple primitive bundles:

```text
R, L, C, R||L, R||C, L||C, R||L||C
```

They respectively contain one, two or three components. For a total component
budget `N`, every source support has at most `N` edges.

### Exact raw-assignment count

For one edge, the generating polynomial by component count is:

```text
p(x) = 3x + 3x^2 + x^3 = (1 + x)^3 - 1.
```

Let `S_e` be the number of terminal-relevant support classes with exactly `e`
edges. The number of permitted bundle assignments to one such support is:

```text
A(N, e) = sum from k=e to N of coefficient(x^k, p(x)^e).
```

The exact raw-assignment total is therefore:

```text
R_N = sum from e=1 to N of S_e A(N, e).
```

This calculation is inexpensive once the relevant-support counts are known.
It does not require constructing or reducing any assigned network.

The observed relevant-support sequence is:

| Edges `e` | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `S_e` | 1 | 1 | 2 | 4 | 10 | 27 | 80 | 258 | 890 | 3,262 |

For reference, the complete support census at the two new levels is:

| Edges | Basic supports | Terminal supports | Relevant supports |
|---:|---:|---:|---:|
| 9 | 710 | 14,376 | 890 |
| 10 | 2,322 | 58,957 | 3,262 |

### Network reduction and uniqueness

For every accepted raw assignment, the current network census calls the public
canonical reduction function. That function:

1. validates the graph, terminals and complete edge assignment;
2. checks connectedness and terminal relevance;
3. creates a factor-labelled NetworkX multigraph;
4. repeatedly merges parallel edges and suppresses non-terminal degree-two
   nodes;
5. tries both terminal orientations and every permutation of the remaining
   internal nodes; and
6. serialises the least result as the canonical reduced signature.

The signature is inserted into a global dictionary. The dictionary therefore
removes duplicates arising from support automorphisms, local series/parallel
reduction and different source supports.

After the main traversal, the implementation separately calculates raw
assignment and assigned-support diagnostics. Those operations repeat support
generation and analysis that the main traversal has already performed.

## Measurements and predictions

### Measured counts and times

| `max-rlc` | Raw assignments | Assigned-support classes | Networks | Time |
|---:|---:|---:|---:|---:|
| 4 | 589 | 364 | 119 | 0.176 s |
| 5 | 4,537 | 2,809 | 632 | 0.594 s |
| 6 | 38,909 | 25,069 | 4,130 | 7.147 s |
| 7 | 362,981 | 247,624 | 32,813 | 55.380 s |
| 8 | 3,657,404 | 2,635,399 | 302,102 | 669.767 s |

All three totals correlate strongly with time because they grow together. Raw
assignments are the most useful causal measure: each one currently invokes the
full canonical reduction path. Across the larger runs, time per raw assignment
is reasonably stable.

### Exact totals at nine and ten components

Using the exact formula and the measured support counts gives:

```text
R_9  =  39,430,084
R_10 = 450,941,128
```

At `N = 9`, the known one- through eight-edge supports contribute 21,912,214
assignments. The 890 nine-edge supports contribute:

```text
890 * 3^9 = 17,517,870.
```

At `N = 10`, the known one- through nine-edge supports contribute 258,323,290
assignments. The 3,262 ten-edge supports contribute:

```text
3,262 * 3^10 = 192,617,838.
```

The largest two support-edge levels contribute about 83.1% of the work at
`N = 9` and 81.6% at `N = 10`.

### The factorial approximation

The simple approximation:

```text
R_N approximately equals (N + 2)!
```

is surprisingly accurate around seven to nine components, but the ten-element
result starts to diverge:

| `N` | Exact raw assignments | `(N + 2)!` | Prediction error |
|---:|---:|---:|---:|
| 8 | 3,657,404 | 3,628,800 | -0.78% |
| 9 | 39,430,084 | 39,916,800 | +1.23% |
| 10 | 450,941,128 | 479,001,600 | +6.22% |

It remains a useful mental sizing rule over this range. There is not enough
evidence to describe it as an asymptotic result.

## Where the current time is likely spent

The current hot loop contains several kinds of repeated work.

### Public validation is repeated for trusted internal objects

The public canonical signature API appropriately validates arbitrary caller
input. The census, however, passes supports that it has just generated and
validated. For every raw assignment it nevertheless repeats:

- graph simplicity and connectedness checks;
- construction and comparison of edge-key sets;
- completeness checks for the assignment; and
- terminal relevance testing by enumeration of simple terminal paths.

The terminal relevance result depends only on the support and terminal pair,
not on its bundle assignment. It should be calculated once per support.

The public API should retain its validation. The census should use a private
trusted-input evaluator after one explicit support preparation step.

### NetworkX graphs are reconstructed and reduced repeatedly

Every assignment reconstructs a labelled multigraph and discovers the same
structural series and parallel reductions. For a fixed support and terminal
pair, the reducible nodes, structural edge combinations and remaining internal
node permutations do not change with the primitive labels.

The structural work can therefore be compiled once. A prepared support could
contain:

- a fixed ordered edge list;
- edge-permutation generators for terminal-preserving automorphisms;
- a reduction expression or instruction sequence describing how original
  edge factors combine;
- the final structural multigraph; and
- precomputed terminal orientations and internal-node serialisation maps.

Evaluating an assignment would then mostly substitute seven small factor
values into a prepared expression and sort or intern the resulting tuples. It
would not copy and repeatedly mutate NetworkX graphs.

### Assignment automorphisms are removed late

At eight components, 3,657,404 raw assignments reduce to 2,635,399 assignment
classes after quotienting by terminal-preserving support automorphisms. The
present network census nevertheless reduces every raw assignment.

Enumerating one canonical representative from each assignment orbit would
reduce the number of reductions by a factor of about 1.39 at that level. This
gain is useful but not transformative because most larger supports have small
automorphism groups.

Burnside's lemma provides orbit counts but not representatives. The network
census needs either:

- canonical assignment generation under the induced edge-permutation group;
  or
- a per-support set of canonicalised assignment tuples.

The latter is simpler but may use substantial memory. A canonical augmentation
or orderly generation method is preferable if it can be kept clear and
testable.

### Diagnostics repeat enumeration

The main traversal already knows every support and raw assignment it visits.
It should accumulate the raw totals directly. Assigned-support diagnostics can
be calculated from the prepared supports and their automorphism data without
regenerating the entire support census.

The report should distinguish diagnostic optimisation from semantic changes:
diagnostic counts must remain identical and should be checked against the
independent census APIs in tests.

### The traversal is naturally parallel

Terminal-relevant supports are independent until their signature sets are
merged. They can be partitioned between worker processes. Processes are more
appropriate than Python threads for this CPU-bound Python and NetworkX work.

Each worker should return a compact set or sorted stream of interned signatures
and component counts. The parent can merge them deterministically. Work should
be partitioned using estimated assignment counts rather than the number of
supports, because supports with different edge counts have very different
costs.

Parallel execution needs an explicit process-count option and a serial default
or well-documented automatic default. Tests must confirm that output is
identical for one and several workers.

## Proposed staged optimisation

### Stage 1: measure and remove avoidable repeated work

Add low-overhead profiling counters or a benchmark harness that separates:

- support generation and terminal analysis;
- assignment generation;
- validation;
- graph construction and local reduction;
- canonical node relabelling and serialisation;
- signature-set insertion and merging; and
- post-census diagnostics.

Then introduce a prepared-support object and a private trusted evaluator. Keep
the public validated API unchanged and test both routes against each other.

Expected effect: likely several-fold, but it should be measured. Merely reusing
diagnostic work is likely to save only a small fraction. Removing path
enumeration, graph validation and NetworkX reconstruction from hundreds of
millions of hot-loop iterations is the important part.

### Stage 2: compile the local-SP reduction plan

Represent the reduction of a fixed support as operations over edge-factor
indices rather than graph mutations. Precompute all structural canonical
relabellings. Intern primitive and common compound factors so equality,
ordering and hashing operate on compact tuples or integer identifiers.

This stage should preserve exactly the current `local-sp` signature. A useful
verification strategy is exhaustive comparison with the existing evaluator at
small bounds and random differential comparison at larger bounds.

Expected effect: a plausible combined improvement of roughly 3 to 15 times
over the current serial implementation, depending on how much time profiling
attributes to validation and NetworkX object manipulation.

### Stage 3: enumerate assignment-orbit representatives

Use the already-computed terminal-preserving edge permutations to avoid
reducing assignments that differ only by a support automorphism.

At eight components, the observed raw-to-orbit ratio places the direct gain at
about 1.39 times. Similar gains, perhaps about 1.2 to 1.5 times, are a sensible
expectation at nine and ten components unless new measurements show otherwise.

### Stage 4: parallelise across prepared supports

Add deterministic multiprocessing with cost-balanced batches. On a machine
with four useful worker cores, a 3 to 3.8 times speed-up may be realistic. With
eight useful cores, 5 to 7 times may be realistic if memory bandwidth and
signature merging do not dominate.

Do not assume that the logical CPU count is the useful worker count. Benchmark
one, two, four and eight workers, and monitor peak memory.

### Stage 5: cache reusable support analysis

Persist or memoise prepared support data by edge count and model version. A
cache entry needs enough version information to prevent reuse after changes to
support relevance, terminal equivalence, bundle semantics or signature
definition.

Caching will greatly improve repeated commands and nearby queries. It will not
by itself remove the first-run cost of evaluating hundreds of millions of
assignments.

## Approximate improvement bounds for `--max-rlc 10`

The measured per-assignment rate predicts roughly 19 to 23 hours. The following
ranges are engineering estimates, not independently measured bounds:

| Implementation | Plausible gain | Approximate time at `N = 10` |
|---|---:|---:|
| Current serial implementation | 1x | 19 to 23 hours or more |
| Trusted evaluator, limited compilation | 2x to 5x | 4 to 12 hours |
| Fully compiled reduction evaluator | 3x to 15x | 1.3 to 7.7 hours |
| Compiled evaluator plus four workers | 8x to 30x | 38 minutes to 2.9 hours |
| Compiled evaluator, orbit generation and effective parallelism | 10x to 40x | 29 minutes to 2.3 hours |

The table should not be read as multiplicative guarantees. Several gains
overlap. The upper end assumes that current graph validation and reconstruction
dominate and that signature merging scales adequately. The lower end should be
used for planning until a profile and prototype exist.

An optimistic specialised implementation might exceed 40 times, but memory
usage, factor interning and global deduplication could become the new limits.

## Alternative: grow canonical networks by mutation

### Growing support graphs

A support tree could start with a one-edge two-terminal graph and apply
operations such as:

- subdividing an edge;
- adding an edge between existing nodes;
- adding an internally disjoint path between existing nodes; and
- composing terminal-relevant blocks in series.

This is not entirely different from the current support generator. The current
generator already grows connected simple graphs by adding a leaf edge or a
missing edge and then removes isomorphic duplicates. Its weakness is that it
generates general connected graphs before choosing terminals and filtering for
terminal relevance.

A better support generator could use a canonical-parent test and generate only
terminal-relevant two-terminal graphs. Structural results suggest decomposing a
terminal-relevant graph into a series chain of blocks and generating cyclic
blocks by ear addition. A complete construction and unique canonical parent
would need to be proved.

This would improve support generation, but support generation is not the main
`--max-rlc 10` cost. There are only 3,262 relevant ten-edge supports but about
451 million raw assignments. Support-only improvement cannot remove the latter
factor.

Using a specialised canonical graph generator, such as a nauty/Traces-based
backend, is also worth evaluating. It may be considerably faster than repeated
NetworkX isomorphism tests, but it would add a dependency or optional external
backend and would not solve assignment enumeration by itself.

### Growing assigned or reduced networks directly

A more radical generator would make canonical reduced networks its states. It
could start from an empty or one-component root and apply mutations such as:

- add an R, L or C branch between existing nodes;
- subdivide a branch and insert an R, L or C element;
- add a new internal path or branch;
- add a primitive in parallel with an existing branch; and
- introduce a new node while preserving the terminal pair.

After every mutation, it would calculate the canonical `local-sp` signature.
A visited map would prevent expansion of an already-seen state at an equal or
greater resource cost.

The attraction is clear. At `N = 8`, the current process evaluates about 12.1
raw assignments for every final unique network. If a direct generator produced
only a small number of candidates per unique state, its work could be much
closer to the output size than to the raw source size.

### Why a visited set is not sufficient

A state may have many parents and mutations may produce many siblings that
canonicalise to the same result. The visited set prevents repeated expansion,
but it does not avoid constructing, reducing and looking up all those duplicate
children. Without an orderly or canonical augmentation rule, the candidate
count can still approach or exceed exhaustive enumeration.

For a dependable improvement, every non-root canonical state should ideally
have one canonical parent. A candidate child would be accepted only when the
inverse of its chosen canonical construction recovers that parent. This is the
same broad principle used in canonical graph generation.

### Completeness and congruence questions

Before using direct network growth for authoritative counts, the following
points need proofs or exhaustive validation:

1. **Complete mutations.** Every network in the intended source-constrained
   result must be reachable from the root.
2. **Safe canonical states.** Locally reducing an intermediate network must not
   remove information needed to reach a distinct later network.
3. **Congruence.** The `local-sp` relation must be compatible with every growth
   operation. Equivalent parents must have equivalent sets of relevant
   children.
4. **Resource history.** The query constrains generating source assignments,
   whereas the reported table counts components in final reduced signatures.
   Two paths to the same signature may use different source resources.
5. **Profile support.** With separate R, L, C or L+C bounds, one scalar minimum
   cost is insufficient. The visited state may need a Pareto frontier of
   non-dominated `(R, L, C, support edges)` resource profiles.
6. **Terminal relevance and simplicity.** Mutations must preserve or correctly
   test the source support rules, including the absence of loops and duplicate
   support edges.

For `--max-rlc` alone, retaining the smallest known source component count for
each canonical state may be sufficient if equivalence is a congruence and all
mutations add non-negative cost. That proposition should be proved rather than
assumed.

### Feasibility assessment

Direct network growth is feasible as a research prototype and potentially much
more efficient. It should not immediately replace the exhaustive
implementation.
The existing method is valuable as a reference oracle for small bounds.

A sensible experiment is:

1. define a deliberately small complete mutation set;
2. implement canonical state and resource-profile storage;
3. compare every result through `--max-rlc 6` or `7` with the existing census;
4. measure generated candidates, accepted states and duplicate children;
5. investigate a canonical-parent rule; and
6. extend the comparison one level at a time.

If candidate-to-state ratios remain small and exact agreement is maintained,
the approach could replace raw assignment traversal for counting. If duplicate
mutation paths explode, the compiled exhaustive evaluator remains the safer
production strategy.

## Recommended order of work

1. Add profiling and exact performance fixtures for `--max-rlc 6` through `8`.
2. Add prepared supports and a trusted internal evaluation path.
3. Compile structural local-SP reduction and canonical relabelling.
4. Add deterministic multiprocessing and measure scaling.
5. Add assignment-orbit representative generation if its measured saving
   justifies the complexity.
6. Cache prepared supports and diagnostic data.
7. In parallel as a research task, prototype direct canonical network growth
   and compare it exhaustively with the reference implementation.

The first six steps preserve the current enumeration semantics and can be
introduced incrementally. The final step has the greatest potential upside,
but also carries the greatest risk of silently omitting or miscounting network
classes.

## Suggested acceptance criteria

Any optimisation of the authoritative census should satisfy all of the
following:

- exact agreement with existing support, raw assignment, assigned-support and
  network totals at all currently practical bounds;
- identical stable signature sets for exhaustive comparison bounds;
- deterministic results independent of worker count and processing order;
- no change to public validation behaviour;
- peak memory recorded alongside runtime;
- separate reporting of first-run and warm-cache performance; and
- benchmark results committed with the machine, Python and dependency versions
  needed to interpret them.

The raw-assignment formula and the totals 39,430,084 and 450,941,128 should be
added as independent checks. They provide inexpensive guards against accidental
changes to the source assignment language while the network evaluator is being
optimised.
