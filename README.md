# 0007-AUV_Code
This is a not actually forked version of the KSU AUV 2024-2025 Software that I am working with.

'-' in a filename means not complete yet. working on it. 

## The way we want this to work.

## The below flowchart represents how we want the program setup during full operation
```mermaid
flowchart TB
    C["Manual Control"] --> n1["Database"]
    D["RL Model Input"] --> n1
    n3["Hardware Interface<br>(Real World and Sim)"] --> A(["Unity Sim"]) & n7(["Real World"])
    n2["AI Package<br>(Camera Vision Code)"] --> n1
    n4["Movement Package<br>(Eventually Sim)<br>(Real World and Sim)"] --> n1
    n5["Sonar Package<br>(Real World Only)"] --> n1
    n6["Hydrophone Package<br>(Eventually)<br>(Real World Only)"] --> n1
    n3 <--> n1
    n1@{ shape: db}
    n3@{ shape: subproc}
    n2@{ shape: subproc}
    n4@{ shape: subproc}
    n5@{ shape: subproc}
    n6@{ shape: subproc}
```
---

## 