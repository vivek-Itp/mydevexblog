# Post queue

The scheduled drafting job takes the first topic marked `[ ]`, writes a draft post
for it, opens a pull request, and changes the mark to `[x]` with the PR number.
Reorder, add, or remove topics freely. One line per topic.

Format: `- [ ] Title | category | two or three lines of angle, in plain words`

Allowed categories: CI/CD, Kubernetes, Platform Engineering, Developer Experience, Observability, Tooling

## Queue

- [ ] Golden paths that people actually take | Platform Engineering | Why templates and paved roads get abandoned, and what keeps developers on them without mandating it.
- [ ] The support channel is your best product research | Developer Experience | Reading the platform Slack channel as a signal. Which questions repeat, what they reveal, and how to turn them into fixes instead of answers.
- [ ] Observability for developers, not just for on-call | Observability | Most dashboards are built for the operator. What a developer needs to see about their own service in the first five minutes after a deploy.
- [ ] Secrets management that developers do not route around | Tooling | When the secure path is harder than the insecure one, people take the insecure one. Making the right way the easy way.
- [ ] Local development environments that match production closely enough | Developer Experience | How far parity needs to go, where it stops being worth it, and the cost of getting it wrong in either direction.
- [ ] Deprecating a platform feature without losing trust | Platform Engineering | Removing something teams depend on. Timelines, migration help, and what happens when a deprecation is announced and then never enforced.
- [ ] Measuring developer experience without a survey | Developer Experience | Lead time, re-run rate, time to first deploy, support volume. Numbers that reflect daily friction and how to collect them without a new tool.

## Drafted

- [x] Kubernetes for people who did not ask for Kubernetes | Kubernetes | Developers want to deploy, see logs and roll back. What the cluster asks of them instead, where the abstraction leaks, and what to put in front of it. | drafted 2026-09-05
- [x] Self-service on a slide vs self-service in practice | Platform Engineering | The gap between an internal platform called self-service and the number of tickets it takes to get a new service running. What to measure to expose the gap. | drafted 2026-09-07
- [x] Error messages are part of the platform | Developer Experience | The one line a developer reads when something fails is the platform's real user interface. How to write errors that say what broke, why, and what to do. | drafted 2026-09-09
- [x] Verifying commit signatures in the CI pipeline | CI/CD | Why signed commits matter, how to enforce verification in the pipeline rather than only in the repo settings, and what breaks for developers when you turn it on. | notes: SSH-signed commits; public keys in parameter store; GitLab runner verifies each new commit against the author key; branch protection plus pipeline check on MR and on promotion to staging over the full range since last merge; crypto application with zero-trust policy; runner signs JAR with KMS key on publish to Nexus; rebases, bots, rotation and new laptops all broke it, fixed with force push on feature branches and holding old and new keys; keys verified per developer, enforcement date with cutoff so older commits ignored; key maintenance automation still missing. | drafted 2026-09-09
