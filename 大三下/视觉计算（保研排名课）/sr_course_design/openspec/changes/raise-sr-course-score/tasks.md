## 1. Experiment Pipeline Improvements

- [x] 1.1 Add optional `patches_per_image` to `TrainConfig` and YAML configs with backward-compatible default behavior.
- [x] 1.2 Update training sample creation so each eligible LR/HR pair can produce multiple aligned random patches.
- [x] 1.3 Add optional `edge_weight` to `TrainConfig` and pass it into `CombinedLoss`.
- [x] 1.4 Add optional learning-rate scheduler support or a documented staged learning-rate strategy that remains CPU-friendly.
- [x] 1.5 Add fairer SRCNN and IMDN config files using comparable epoch and batch settings where runtime permits.
- [x] 1.6 Add edge-weight ablation config files for no-edge and multiple edge weights.
- [x] 1.7 Ensure old config files continue to run without modification.

## 2. Evaluation and Evidence Assets

- [x] 2.1 Update report asset generation so training curves use complete intended runs or explicitly label selected run segments.
- [x] 2.2 Add an ablation chart or table generated from CSV metrics for edge-weight comparison.
- [x] 2.3 Add a helper or documented command pattern for benchmark-compatible evaluation on Set5, Set14, BSD100, and Urban100 style LR/HR folders.
- [x] 2.4 Add visual comparison generation for both best-case and failure-case examples.
- [x] 2.5 Preserve existing DIV2K validation results and write new outputs under distinct filenames.
- [x] 2.6 Add clear captions for real evidence figures that identify dataset, method, and metric source.

## 3. Run Strengthened Experiments

- [x] 3.1 Run smoke tests for SRCNN and IMDN after training pipeline changes.
- [x] 3.2 Run focused unit tests for dataset, model, metric, and inference behavior.
- [x] 3.3 Train or rerun fairer SRCNN baseline configuration if runtime is acceptable.
- [x] 3.4 Train or rerun IMDN no-edge configuration with improved sampling if runtime is acceptable.
- [x] 3.5 Train at least two edge-weight ablation configurations if runtime is acceptable.
- [x] 3.6 Run inference and evaluation for every completed experiment.
- [x] 3.7 Regenerate report figures from the resulting CSV and image outputs.

## 4. Literature and Bibliography

- [x] 4.1 Add BibTeX entries for recent representative SR methods such as SwinIR, HAT or DAT, Real-ESRGAN, StableSR, DiffIR, and SeeSR.
- [x] 4.2 Rewrite related work to include classic CNN, lightweight SR, Transformer SR, real-world GAN SR, and diffusion-prior SR.
- [x] 4.3 Add deeper analysis for at least three representative papers, covering mechanism, motivation, strengths, weaknesses, and relation to this project.
- [x] 4.4 Add a compact literature comparison table with method type, representative model, core mechanism, strength, limitation, and implementation feasibility.
- [x] 4.5 Explain why the implementation remains IMDN-style under CPU and course constraints despite newer methods.

## 5. Report Restructuring

- [x] 5.1 Add a section explicitly mapping the report to the six course grading criteria.
- [x] 5.2 Add a section distinguishing reproduced work, project implementation work, and exploratory improvement work.
- [x] 5.3 Rewrite the edge-loss section so it is framed as an exploratory structural constraint rather than a proven novel algorithm.
- [x] 5.4 Add an experiment fairness and limitations section explaining short training, sampling coverage, model capacity, missing benchmarks, and metric limitations.
- [x] 5.5 Add a next-step plan table covering longer training, multi-patch sampling, scheduler, benchmark evaluation, perceptual metrics, and stronger improvement modules.
- [x] 5.6 Reduce or reposition generated schematic figures so real experiment artifacts carry the main evidential load.
- [x] 5.7 Replace placeholder team contribution text with concrete names or identifiers if the user provides them; otherwise mark it as a required final-submission edit.

## 6. Verification and Final Packaging

- [x] 6.1 Compile the LaTeX report with `xelatex` and `bibtex` as needed until references and citations resolve.
- [x] 6.2 Check the LaTeX log for errors, undefined references, and undefined citations.
- [x] 6.3 Run available tests and record any environment-specific failures separately from project failures.
- [x] 6.4 Verify that every reported numeric result is traceable to a CSV file or command output.
- [x] 6.5 Produce a final summary of completed improvements and remaining constraints for the user before submission.
