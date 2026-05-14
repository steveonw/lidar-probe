# scene_probe

**Closed-loop active perception built on [scene_lens](https://github.com/USERNAME/scene_lens).** Hypothesis → render → score → perturb → accept-or-reject → choose next view → repeat. Pure numpy + Pillow. Gradient-free.

![Probe convergence: truth → wrong hypothesis → fitted scene](assets/probe_convergence.png)

*Row 1: ground-truth scene from three views. Row 2: deliberately-displaced hypothesis ("BEFORE"). Row 3: hypothesis after 120 probe iterations ("AFTER"). The sphere and cylinder converge to within ~0.15 units of truth; the blue box hits a local minimum (honest behavior for hill climbing, fixable with restarts or simulated annealing).*

## What it is

`scene_lens` answers *"does this scene contain what I claimed?"* — it's a verifier. `scene_probe` answers *"given what I'm seeing, what scene am I actually looking at?"* — it's a fitter. The same engine runs both directions, with the loop on top.

The loop:

```
        ┌────────────────────────────────────────────────┐
        │                                                │
        ▼                                                │
 hypothesis ──→ render at current view ──→ predicted image
                                                         │
                                                         │
 observed image  ───────────────────────────────────→ compare
                                                         │
                                                         ▼
                                               accept/reject perturbation
                                                         │
                                                         ▼
                                          pick next view (max residual error)
                                                         │
                                                         └──→ next iter
```

Gradient-free because `scene_lens` isn't differentiable — hard primitive choices (which primitive does this ray hit?) break autograd. The loop uses random perturbation + accept-or-reject (hill climbing). Slower than NeRF or differentiable rendering, but produces **editable symbolic scenes** instead of opaque neural fields. The output is `[Primitive(box, center=[...], ...), Primitive(sphere, ...)]` — data an LLM agent can read, modify, and reason about.

## Quick start

```bash
pip install -e .  # also installs scene_lens
python examples/fit_simple_scene.py
```

Minimal usage:

```python
from scene_lens import Scene, Primitive
from scene_probe import Probe, observe_from_scene, build_orbit_cameras, build_report

truth = Scene(primitives=[...])  # the "real" scene
cams = build_orbit_cameras(n=8, radius=7.0)
observations = [observe_from_scene(truth, c) for c in cams]

hypothesis = Scene(primitives=[...])  # initial wrong guess
probe = Probe(hypothesis=hypothesis, observations=observations,
              perturb_pos_sigma=0.4, replan_every=4)

fitted, history = probe.run(max_iters=120, tolerance=0.5, verbose=True)
report = build_report(probe)
print(f"error: {report.initial_error} → {report.final_error}")
print(f"reduction: {report.error_reduction_pct}%")
```

## What the probe does, step by step

At each iteration:

1. **Choose a viewpoint.** Every `replan_every` iterations, the probe re-evaluates which observation is most contradicted by the current hypothesis and switches focus there. Between re-plans, the probe hammers the same view to make incremental progress. This is *active sampling of disagreement* — the engine spends compute where it's most wrong.

2. **Propose a perturbation.** Random walk: pick one primitive, jitter its position (Gaussian, σ = `pos_sigma`) and/or its size (log-normal, σ = `size_sigma`). No gradients; the perturbation is uncorrelated with the error signal.

3. **Score the perturbation.** Render the candidate hypothesis from the current view, compute mean L1 pixel distance against the observation.

4. **Accept or reject.** If the perturbed scene scores lower error, keep it. Otherwise revert. This is greedy hill climbing — simplest gradient-free algorithm that works.

5. **Log and check stop conditions.** Append the step to history (for plotting and reporting). If error < tolerance, converged. Otherwise repeat.

## Honest limitations

- **Local minima.** Hill climbing can get stuck. The blue box in the demo image is an example — it got moved out of frame and never recovered. Fixes: simulated annealing (accept some bad moves), random restarts, multiple chains. Not implemented in v0.1.0.
- **Performance.** View planning is dominant cost — every `replan_every` iterations, the probe renders the hypothesis from all N candidate cameras. For 8 observations × 4000 rays × 12 candidate cams that's ~50k rays per replan. ~6 seconds for 120 iterations on a 4-primitive scene. Scales poorly with primitive count.
- **Fixed primitive count and type.** v0.1.0 only fits positions and sizes. Doesn't add or remove primitives, doesn't change shape (box → cylinder), doesn't fit rotations or colors. Would all be additions to `perturb_scene()`.
- **L1 pixel error is crude.** Sensitive to lighting, color, and small misalignments. A real implementation should use structural similarity, silhouette-IoU, or the topology-aware error from the `scene_lens` silhouette layer (sketched but not built).
- **Synthetic-only "observations" in this demo.** Real use means lifting photos into `scene_lens` camera space (known intrinsics, pinhole rectification) — straightforward but not included.

## When to use this

- Recovering structured scene representations from a small set of viewpoints, where you want **editable output** rather than a neural field.
- Closing the loop on an LLM agent's generated scene: agent proposes geometry, probe verifies and proposes corrections.
- Robotics/inspection where you have known sensor poses and want to fit primitive models to observations.
- Teaching active perception, predictive coding, or analysis-by-synthesis — the entire loop is ~300 lines of legible Python.

## When NOT to use this

- High-fidelity scene reconstruction (use NeRF, 3D Gaussian Splatting, photogrammetry).
- Real-time anything (use a GPU pipeline).
- Scenes with many primitives (>20) — random hill climbing scales linearly with primitive count; you'd want CMA-ES or differentiable rendering above that scale.

## How this relates to scene_lens

`scene_probe` depends on `scene_lens` for:

- `Camera`, `Scene`, `Primitive` data types
- `fire_burst` and `render_burst` for rendering hypothesis and observation
- The whole BVH + lens machinery

The boundary is clean: `scene_lens` knows nothing about the loop, the perturbation strategy, or the planner. `scene_probe` knows nothing about how rays are cast. Each can be developed and tested independently.

If you ever want to swap out the renderer (e.g., for a differentiable PyTorch version), only `render_hypothesis()` and `observe_from_scene()` in `probe.py` need to change. Everything else is renderer-agnostic.

## Architecture

```
scene_probe/
├── probe.py       # Probe class + step + run + perturbation + planner + error
└── __init__.py    # public API
```

One file, one focused job. The four core operations are functions you can swap independently:

- `render_hypothesis(scene, cam)` — forward render (defaults to scene_lens, override to use a real renderer)
- `image_error(predicted, observed)` — scoring (defaults to L1, override for IoU/SSIM/topology)
- `perturb_scene(scene, rng)` — proposal strategy (override for CMA-ES, simulated annealing, etc.)
- `pick_max_error_view(hypothesis, observations)` — view planner (override for info-gain planning)

## Testing

```bash
PYTHONPATH=. python tests/test_probe.py
```

## License

[MIT](LICENSE).
