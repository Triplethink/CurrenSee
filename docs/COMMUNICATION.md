# Project communication inside the company

## Phase 1: Steps before implementing

1. First, I would go through JIRA, GIT and Slack, to check, if somebody did something currency related in the past. Maybe, there was already some POC 2 years ago? Maybe some other team is already sourcing some exchange rates data from somewhere. _But let's assume for our scenario, that I found nothing_.
2. The next step should be to organize a meeting (or maybe just a PUBLIC Slack channel could be enough) with all key stakeholders to identify both immediate requirements and long-term objectives (see _The main questions for stakeholders_ below).
3. Based on the discussion, I would create a Confluence page with the project description and some user stories to the backlog. As the project is kinda simple, I think something like 2-3 stories could be enough (one for analysis, one for POC and one for the final deployment). The important thing here is that everyone from the engineering team should be able to work on these user stories.

### The main questions for stakeholders
Here is the list of questions I would ask:
1. WHEN do you need it to have it done?
2. HOW OFTEN should the data be updated? Could this change in the future?
3. And doublecheck WHAT should be the main (base) currency, probably USD right?
4. Do we want to PAY for this data?

Let's fake here some outputs from the discussion:
1. _"Of course, we would like to have it ASAP, but end of this Q is fine..."_
2. _"We are fine with daily numbers, but it would be really nice for Data Analysts to have also some historical values (let's say 1-2 years back). It could happen in the future, that the required frequency will be one hour, but for now daily update is more than OK, we are not a bank or something like that."_
3. _"Yes it is USD and it will be USD even in future."_
4. _"NO (if possible)"_

## Phase 2: Research & Implementation
1. The first user story will be about researching the available sources with exchange rates data. NOTE: This could be a job for BI Analyst, for my POC here in this repo I've used Google and AI tools with Deep Research feature - for details you can read [Evaluation Document](docs/EVALUATION.md) document.
2. The research user story has one-two winners, this should be summarized in a Confluence subpage and discussed - first with the engineering team and later with stakeholders. We should doublecheck if the pros and cons of the selected provider are OK for them.
3. Let's say that they like it. We should now also contact somebody in our company who is responsible for (dis)approving usage of external data sources (maybe Head of Data?, CTO or somebody like that).
4. Everything approved, let's start coding (and update Confluence page with the approvals, just for transparency).
5. _<...still coding...>_
6. POC is done, let's create some dev environment and test it there, give access also to some analysts if this is good for them.
7. _"Wow, it is perfect!"_
8. Deploy it (please don't do it on Friday!)

## Phase 3: Deploy & Announcement
1. Finalize the documentation in Confluence
2. Announce the new data source in the project relevant public channel, but we should consider announcing also in some bigger channels related to data.
3. Create a reminder for the team to archive the project related Slack channel in approx. 6 months.
