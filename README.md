# Probabilistic-greedy-method-for-server-scheduling
Part of the greedy algorithm used to solve the 2018 Alibaba Tianchi Competition-Server Dispatch Competition. This method ranks 66 in the preliminary round and is ranked second in the semi-finals. It is a good starting method.
# Big-data-server-scheduling-1
This code solves the scheduling problem of a large number of servers.
The 68219 tasks are scheduled to 6000 servers, taking into account the constraints of the server's cpu, MEM, DISK, and app constraints.
I have tried to use PYHON, MINZINC, GUROBI and other tools to solve, using the firstfit method, localsearch method and random algorithm.

====================================================================================================================================

![1440-天池-en.jpg](https://work.alibaba-inc.com/aliwork_tfs/g01_alibaba-inc_com/tfscom/TB1wvJPoOCYBuNkHFCcXXcHtVXa.tfsprivate.jpg)  

====================================================================================================================================

Alibaba Global Scheduling Algorithm Competition
===============================================

The problem in the preliminary is an abstraction of one of many our scenarios in production, where the number of constraints is reduced. The problem would help participants understand our concern. In the semi-final, we will add more constraints as well as more optimization objectives. The problem for semi-final will not be published until the end of preliminary. For the accurate schedule of the competition, please refer to the introduction.

We look forward to having you and your teammates share your ideas to solve the problem!

Note: The current datasets are for participants to get an idea of the problem. They may be changedlater after more evaluation and possible feedback. The final data will be determined with the annoucement of the evaluation on Aug 20th.

Semi-final is built based on preliminary with some modifications on both data and constraints.

Constraints for rescheduling the instances
------------------------------------------

The rescheduling of instances is more practical. The rescheduling should be executed in multiple rounds, and in each round, there can be many rescheduling actions. A rescheduling is carried out in a create-then-delete manner. For instance:

    1,inst1,A
    1,inst2,A
    2,inst3,B
    

describes a _double-phase_ rescheduling plan. In the 1st round, inst1 and inst2 are rescheduled to machine A (suppose both inst were on other machines), and this is executed as follows. In the first phase, machine A creates new inst1 and inst2, if succeed, inst1 and inst2 are deleted on their original hosts. After these actions, the 2nd round is executed (inst3 to machine B).

If rescheduling fails, the scheduling of inst'sise terminated.

**Constraints on rescheduling**: The is no limit on the number of rescheduling action per round, but there is a limit on the number of rounds k: k<= 3.

scheduling of batch computation workloads
-----------------------------------------

In preliminary, there are only instances from online service applications, whose performance must be guaranteed. One approach on protecting their performance is to maintain the resource utilization at a moderate level (50% in preliminary). However, this approach causes low resource utilization rate. In production, to reach higher resource utilization, some batch computation workloads are deployed too.

A batch task is defined in `job_info.x.csv`, in the form of:

    task_id, cpu, mem, number_of_instances, execution_time, dependency_task_id
    

in which:

*   The unit of execution_time is minute. The 98 time points in cpu/mem curve represent the resource consumption at \[0,15), \[15,30), ..., \[1455,1470) (98 time spans in total)
*   The start time of any instance cannot be earlier than the completion of its dependency task
*   All task instances must be completed within \[0, 1470)
    *   note that for any task, iif all instances for this task are completed, then the task can be considered as completed.
*   Instances of tasks cannot be rescheduled (once scheduled, cannot move)

The valid solution shoud consis of two parts:

*   for application instances: `<scheduling-round_number, instance_id, target_machine_id>`
*   for batch task instances: `task_instance_id, target-machine-id, start_time, number_of_instances_to_start`

Once batch task instances begin to get scheduled, no more rescheduling of application instances is allowed.

Evaluation modification
-----------------------

The evaluation method is updated based on the preliminary, where `a=10` is changed to

    a=(1+<number of inst's on this machine>)
    

Data description
----------------

There are 5 datasets for semi-final: a, b, c, d, e, each representing an individual problem. They are of the same format and constraints, and the differences are their numeric values.

*   app\_interference.csv and app\_resources.csv are shared by all 5 sets of data
*   instance\_deploy.x.csv, job\_info.x.csv, machine_resources.x.csv are the dedicated data for dataset x.

The submission should be in the order of a, b, c, d, e, separated by #

Below is an example:

    1, inst1, machine_a
    task_1, machine_a, 10, 31
    #
    1, inst1, machine_b
    2, inst2, machine_c
    task_1, machine_c, 10, 28
    

The score of a team is the sum of 5 scores.

Preparation for final submission
--------------------------------

The qualification to final is partially determined by the rank in the semi-final. Also, we will ask the top teams in the semi-final to submit their code and a brief document for offline review. We have the following suggestions to the participants:

*   Please organize your code as recommended in the problem description in preliminary (link)
*   Please prepare a brief doc, including:
    *   Your idea on solving the problem
    *   The computation environment (hardware, software, etc) and execution time.
    *   Anything you would like us to know
*   After the semi-final (2018.09.07), we will ask top teams to submit their code and report and we will evaluate them offline for qualification to final. Teams that refuse to provide code and report will not be qualified, however, we sincerely wish you could share with us. Also, you are welcome to send us the code and doc even though you are not invited, and we will have a serious look at them and give you feedback.

**Preliminary Round Task**

  
Important update:

1\. On July 26th, the preliminary is updated as follows:

    \* An additional problem (Data\_B) is added, the original problem is now referred to as Data\_A

    \* Data\_B and Data\_A are two independent problems, but they are of the same format and only differ numerically. The idea behind adding Data\_B is to prevent from an algorithm that is overfitting to Data\_A

    \* By adding Data_B into preliminary, the submission needs updating too, which is described in "submission of work" below. In short, the updated submission format is:

        <Solution to Data_A>

        #

        <Solution to Data_B>

    \* The evaluation method will be updated and applied to the leaderboard on July 30th. Here is the updated evaluation:  final\_score = 0.5*(score(Data\_A)+score(Data\_B)), in which the evaluation of either Data\_A or Data_B remains the same as before, see details in "evaluation and ranking".  The rules on qualification to semi-final remain unchanged (see "Introduction")

    \* We are sorry for the inconvenience of this update and we will try to bring the best experience to the participants. More about the rationale underlying this update can be found at [https://tianchi.aliyun.com/forum/new_articleDetail.html?spm=5176.8366600.0.0.14b3311fg7jiwI&raceId=231663&postsId=5805](https://tianchi.aliyun.com/forum/new_articleDetail.html?spm=5176.8366600.0.0.14b3311fg7jiwI&raceId=231663&postsId=5805)

### 1 Problem description

On July 26th, an additional problem (described by  Data\_B\_xxxx) is added to the preliminary. The problem described by Data\_A (i.e. the original problem) and the problem described by Data\_B are two independent problems. The resulting update in the evaluation (which is mandatory of course) of the preliminary is presented in "Important update" above.

The data used in this competition is sampled from one of our production clusters, including about 6K machines and 68K instances. Some of the instances have already scheduled to the machines while the rest are unscheduled. 

Requirement: Design an algorithm to generate an optimal deployment plan by scheduling all unscheduled instances to machines, and moving some already scheduled instances to another machine (i.e. rescheduling). Note that both scheduling and rescheduling must respect some constraints which are to be presented in the next section. An optimal deployment plan is a plan in which the number of actually used machines is as less as possible while the resource utilization of each machine cannot be too high. See “Evaluation and Ranking (Preliminary)” for more details.

Before going to the description of constraints, 3 objects need to be defined for participants to better understand the scenario.

**_Instance_**: An instance is the object to be scheduled to a machine. In production, an instance may be a docker container.

**_App_**: Each instance belongs to one and only one App (short for “Application”). An App often includes many instances, and all instances belong to one App have same constraints.

**_Machine_**: A machine is a server in our cluster. An instance is said to be scheduled to a machine if the instance is assigned to the machine.

**1.1Constraint description**

The following constraints should be respected when assigning an instance to a machine.

**_（_****_1_****_）_****_Resource constraint._**Each instance has resource constraint with 3 resource dimensions: CPU, Memory and Disk, in which CPU and Memory are given as time curves. Each value in the curve represents the amount of corresponding resource required by the instance at the time point. The constraint is that, at any timestamp T, on any machine A, for any resource type (CPU, Memory or Disk), the sum of resource required by the instances on this machine cannot be larger than the capacity of corresponding resource of the machine.

**_（_****_2_****_）_****_Special resource constraint._**We have 3 special resource types reflecting the importance of instances: P type, M type, and PM type. They are independent resource constraints. For any given machine, the capacity for P, M and PM resources are specified and none can be violated, i.e. the sum of all instances’ P requirement on the machine cannot be larger the P capacity of the machine. Same for M, and PM.

**_（_****_3_****_）_****_Anti-affinity constraint (due to interference)_**. As there are instances from different Apps running on the same machine, there are potential interference between instances from certain Apps and we need to try not put them on the same machine. Such anti-affinity constraint is described in the form of <App\_A, App\_B, k>, which means that if there is one instance from App\_A on a machine, there could be at most k instances from App\_B (k could be 0) on the same machine. App\_A and App\_B could be the same App id (e.g. <App\_A, App\_A, k>), and this means at most k instances from App_A could be on one machine.

**1.2Data Description**

The constraints explained in section “constraint description” are expressed with 4 files: instance\_deply.csv, app\_resource.csv, machine\_resource.csv and app\_intereference.csv. Every line in the files represents one record, while the meaning of each line is introduced as following:

（1）instance_deploy.csv

![屏幕快照 2018-06-11 下午3.46.48.png](https://work.alibaba-inc.com/aliwork_tfs/g01_alibaba-inc_com/tfscom/TB1BjG3h26TBKNjSZJiXXbKVFXa.tfsprivate.png)  


（2）app_resource.csv  

![屏幕快照 2018-06-11 下午3.47.41.png](https://work.alibaba-inc.com/aliwork_tfs/g01_alibaba-inc_com/tfscom/TB1U.JqiXooBKNjSZFPXXXa2XXa.tfsprivate.png)  

  
（3）machine_resource.csv  

![屏幕快照 2018-06-11 下午3.48.34.png](https://work.alibaba-inc.com/aliwork_tfs/g01_alibaba-inc_com/tfscom/TB1kDsyw29TBuNjy1zbXXXpepXa.tfsprivate.png)  

  
（4）app_interference.csv

![屏幕快照 2018-06-11 下午3.49.17.png](https://work.alibaba-inc.com/aliwork_tfs/g01_alibaba-inc_com/tfscom/TB1mLIqwVOWBuNjy0FiXXXFxVXa.tfsprivate.png)  

### 1.3 Submission of work

#### 1.3.1 General Submission Format (Preliminary)

Due to the additional problem (Data_B) updated on July 26th, there is a small change in the submission of work. The new submission format is:

        <Solution to Data_A>

        #

        <Solution to Data_B>

Note that the solution to Data\_A must come before the solution to Data\_B.

The format of the solution to either Data\_A or Data\_B remains and can be found below. An example of the updated submission format of Data\_A and Data\_B can be found in submit_sample.csv.

#### 1.3.2 Submission Format of each problem (Preliminary)

For each problem (i.e. the solution to Data\_A or Data\_B), the solution should be an “instance migration plan”, which is consisted of a serial of placement decisions and every single line represents the placement decision of an instance, started from the first line. An instance can be moved multiple times. The format is as follows:

<instance id, target machine id>

<instance id, target machine id>

<instance id, target machine id>

…

Here is an example:

`instance_1, machine_1`

`instance_2, machine_2`

`instance_3, machine_2`

`instance_4, machine_1`

Requirement:

*   All instances should be placed eventually.
*   Invalid instance id or machine id is not allowed.
*   Please save and submit your file as “submit_<YYMMDD-hhmmss>.csv” <YYMMDD-hhmmss> is the time stamp of your submitted plan. We recommend such naming style.

#### 1.3.3 Evaluation and Ranking (Preliminary)

（1）Evaluate by executing the_instance migration plan_, from top line to the last, to produce the final deployment plan (in which every instance should be assigned with a machine). If any placement decision in the plan violates any of the constraints, the evaluation terminates and we would take the current the deployment plan as final to perform ranking.

（2）Ranking criteria of the deployment plan

*   When a deployment plan is generated, we will calculate its total\_cost\_scoreusing the formulation:   
    ![屏幕快照 2018-06-11 下午3.39.40.png](https://work.alibaba-inc.com/aliwork_tfs/g01_alibaba-inc_com/tfscom/TB1EFnEoOOYBuNjSsD4XXbSkFXa.tfsprivate.png)  
    

#### 1.3.4 How to win

（1）The ranking of preliminary is depended only on the**_total\_cost\_score_**of the submitted_instance migration plan._

（2）Top 100 teams in the preliminary will be qualified to semi-final.

（3）Top 10 teams in the semi-final will be required to submit your code, documentation and a brief report. We will have our algorithm experts to evaluate

（4）More details for semi-final will be released later. However, we always prefer:

Algorithms with less complexity and short execution time (say, less than 1 hour, will be specified with the release of semi-final).

Algorithms with reasonable convergence rate.

Algorithms with good creativity, flexibility and robustness.

#### 1.3.5 Recommended Submission Format in Semi-Final (Draft)

_Note: This may be updated when the problem for semi-final gets online._

For the semi-final, we will also ask the participants to submit the instance\_migration\_plan and rank the results. By the end of the semi-final, top 10 teams on the rank will be asked to provide the code, design doc, etc. for off-line evaluation. Teams that do not provide the required materials will not be qualified to the final. The following is the requirement of submission of your code, and we recommend the participants to arrange your project accordingly to make your submission more enjoyable (see example in Note1).

（1）Data file: data/*.csv

This is where you should put the original input of your algorithm. So please leave this directory empty in your submission. If your algorithm has any intermedia file to generate, you can put them here in your code.

（2）Code file: code/*.py (or any programming language)

It is better to make your input directory in relative path instead of absolute path

You should have main.py or main.ipynb so that the result of your algorithm can be produced by executing it directly (or other equivalent main in other languages)

The result of your code should be written to ../submit/ directory

（3）Output file: submit/*.csv

This is where you should put the result.csv

Please generate your result with time, such assubmit\_Ymd\_HMS.csv(e.g.submit\_20180203\_040506.csv)

（4）Randomness in the code:

If there is any random number / variables used in your program, please set them in your submission. If not set, we will run multiple times and use the average as your submission result. If the error is too far from the submitted result, the team will not be qualified. Please name your results by time (example code in Note2.)

Note1: the directory of project

·project

·|--README.md

·|--data

·|--code

·   |\-\- main.py or main.ipynb or <other languages>

·|--submit

·   |\-\- submit\_20180203\_040506.csv

Note2: recommended file name of your submission

·\# java for example

·import datetime

·data.to\_csv(("../submit/submit\_"+datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv"), header=None, index=False)

### 1.4 You Could Do More …

What is described in this section is NOT part of requirement of the competition.

The idea of us hosting this competition is not only having some winners, we would also like to share a practical case for enthusiasts in related area to have more fun playing with our data. The following ideas are left for you to explore. They do not count as part of the competition, but we are keen to hear your ideas on these scenarios.

（1）Very similar to the formal competition, only that you could design an online algorithm instead of this offline one. The difference is that, in our given scenario, designer has full knowledge of what to schedule and could manipulate on the sequence of instances to schedule. However, for an online algorithm, scheduler can only schedule instance one by one and does not have knowledge on which one among the many type of instances to come next while scheduler cannot deny an instance to be scheduled (not at all or for too long, depending on the assumption you make).

（2）Make the algorithm more robust. As you may have noticed, we use time curves to describe the resource requirement of CPU and Memory. The curves are generated with our estimation model based on the historical data we sampled for every application. In production, it is very likely that the actual resource consumption does not meet the estimation. How can you design robust algorithm that leads to optimal solution despite such error?

（3）Any wild thoughts you would like to play with the data. If you are interested in this, we are sure you would have more fun in the second phase of our competition. Please stay tuned!

# Code description

## how to run this code 

### firstfit
if you want to run firstfit method run:

python3 newfirstfit.py [a,b,c,d,e] [n]

a,b,c,d,e is the name of the data, and n is the number of machine to be cut.

### probabilistic greedy

if you want to run firstfit method run:

python3 chpartgreedy.py [a,b,c,d,e] [n]

a,b,c,d,e is the name of the data, and n is the number of machine to be cut.