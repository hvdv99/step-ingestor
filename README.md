# StepBoard

This application lets users analyse their step data collected from their polar device.


# Iteration 1
_"Build system quick, then iterate"_

## Goal
Create simple but secure application

## Requirements
### Functional
* User can log in/ out
* User can delete account and data
* User can visualize steps data

### Structural
* Architecture: Monolith
* Clean coding practices
* Security: 
  * API: O2Auth, HTTPS prevent XSR
* Monitoring: ?
* Testing: Load test and authorization 
* Deployment: CI/CD

## Architecture

## Tech stack
* pgSQL
* SQL Alchemy
* alembic
* Authlib
* Flask

##  References
* https://www.polar.com/accesslink-api/#polar-accesslink-api
* https://refactoring.guru/design-patterns/adapter
* https://flask.palletsprojects.com/en/stable/web-security/
* https://www.cosmicpython.com/book/chapter_02_repository.html
* 

## Log
* Day 1: Test OAuth Workflow from Polar Example repository (DONE)
* Day 2: Setup up Postgres DB with timescale extension (DONE)
* Day 3: Create endpoint for retrieving steps (DONE) -> Scope creep due to Open API Spec
* Day 4: Connect API with DB (DONE 24/09/25)
* Day 5: Insert logic for populating the DB with historical data when running the application: 
  * Extent `/users/activities` with parameters for `from / to` to retrieve data from specified period. (DONE)
  * Write function in _service layer/polar_adapter_ to create sliding windows (max. 28 days) for the available period (365 days). Calculate number of requests. (DONE)
  * Write function: `populate db` in _service_layer_ -> think of tests before you do execute because there is only a limited number of requests per hour. (DONE)
* Day 7: Set up CI/CD in GitHub Actions
* Day 14: Push as first version to Github




