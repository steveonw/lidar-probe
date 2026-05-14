# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-05-14

First public release. Closed-loop active perception built on `scene_lens`.

### Added
- `Probe` class implementing hypothesis → render → score → perturb →
  accept/reject → choose next view → repeat. Pure numpy, gradient-free
  hill climbing.
- `Observation` dataclass holding a `(camera, image)` pair. Synthetic
  observations via `observe_from_scene`; real photos supported by
  constructing `Observation` directly.
- `perturb_scene(scene, rng)` — random walk on primitive position
  (Gaussian) and size (log-normal). Returns a new Scene; does not mutate
  input.
- `pick_max_error_view(hypothesis, observations)` — naive next-best-view
  planner: render hypothesis at every candidate camera, pick the one
  where it's most wrong.
- `build_orbit_cameras(n, radius, height)` — helper to produce a ring of
  pinhole cameras around a target.
- `image_error(predicted, observed)` — mean L1 pixel distance. Cheap
  baseline; swap for SSIM, IoU, or silhouette-topology error in subclasses.
- `build_report(probe)` — JSON-serializable structured summary of a probe
  run. Suitable for handing to an LLM agent.
- Example: `examples/fit_simple_scene.py` — recovers a 4-primitive scene
  from 8 orbiting views. Produces a convergence figure and error curve.
- Test: `tests/test_probe.py` — 18 unit tests covering error function,
  perturbation properties, planner behavior, end-to-end convergence on a
  1-primitive scene, and report serialization.

### Bugs caught during build
- `list.index()` lookup on `Observation` objects raised numpy `__eq__`
  ambiguity because dataclasses with `np.ndarray` fields can't be compared
  for equality directly. Fixed by passing the view index explicitly
  through `step()` and using identity (`is`) for re-plan lookups.

### Known limitations (documented in README)
- Hill climbing gets stuck in local minima. Demo image shows one
  primitive that didn't recover. Fixable with simulated annealing or
  random restarts (not in v0.1.0).
- View planning is the dominant cost — every replan re-renders the
  hypothesis from N candidate cameras. ~6 seconds for a 4-primitive, 8-
  observation, 120-iteration run.
- Only fits position and size. Doesn't add/remove primitives, change
  shape type, fit rotation, or fit color.
- L1 pixel error is crude; sensitive to lighting and small misalignments.

### Roadmap (not committed)
- Simulated annealing: accept some uphill moves to escape local minima.
- CMA-ES proposer: smarter than random walk, fewer wasted samples.
- Info-gain view planner: replace `max_error` heuristic with expected
  entropy reduction over the hypothesis posterior.
- Silhouette + topology error from `scene_lens` roadmap: replace L1 pixel
  diff with primitive-level structured error.
- Multi-chain probe: run several probes in parallel from different
  starting points, report the best.
- Real-image observations: rectification and camera calibration helpers
  so real photos can be used directly.
