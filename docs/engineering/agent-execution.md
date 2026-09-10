# Agent Execution

Before assigning a task to an agent:

1. confirm the task is READY;
2. calculate dependencies;
3. detect overlapping artifacts;
4. place the task in a safe execution wave;
5. build the task context subgraph;
6. allocate a worktree when parallel execution is used.

After implementation:

1. run tests;
2. create/update the PR;
3. synchronize PR/Git changes to the graph;
4. run drift and impact checks;
5. merge only after governed invariants pass.
