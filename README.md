# restaurant-search-service

### APIs Implemented

1. Get /recommend (Auth: None)

    Request: curl '/recommend?query=A%20vegetarian%20Italian%20restaurant&requestTime=2024-12-29%2019%3A54%3A37.273202-06%3A00'
    * query: Hold the sentence to pass (required)
    * requestTime: DateTime with timezone of when the reqest was made (required)
    * nextPage: If result is more than 20, use nextPage to get the next page of recommendation
    
    Output:
    ```
    {
        "restaurantRecommendation": [
            {
                "name": "test1", 
                "style": "italian", 
                "address": "address1", 
                "openHour": "00:00:00-05:00", 
                "clouseHour": "23:00:00-05:00", 
                "vegetarian": true, 
                "delivers": true
            }, 
            {
                "name": 
                "test2", 
                "style": 
                "italian", 
                "address": 
                "address1", 
                "openHour": 
                "00:00:00-05:00", 
                "clouseHour": 
                "23:00:00-05:00", 
                "vegetarian": true, "delivers": true
            }
        ]
        nextPage: 2
    }
    ```        
2. POST /restaurant (Auth: X-AUTH-API-KEY header): Persist restaurants to the database in batches of 50 (Batch size is configurable)
    
    Body:
    ```
    {
        "records" : [
            {	
                "name": "test1",
                "style": "Italian",
                "address": "address1",
                "openHour": "00:00",
                "closeHour": "12:00",
                "vegetarian": "true",
                "delivers": "true",
                "timezone": "America/Chicago"
            },
            {	
                "name": "test2",
                "style": "French",
                "address": "address2",
                "openHour": "00:00",
                "closeHour": "23:00",
                "vegetarian": "true",
                "delivers": "true",
                "timezone": "America/Chicago"
            }
        ]
    }
    ```
    Response: 
    ```
    {
        "statusCode": 201,
        "body": {"message": "Successfully created X records"}
    }
    ```
3. PUT /restaurant (Auth: X-AUTH-API-KEY header): Update the a restaurant. Name and Address cannot be updated.
    
    Body:
    ```
    {
        "record": {	
            "name": "test2",
            "style": "korean",
            "address": "address2",
            "openHour": "00:00",
            "closeHour": "14:00",
            "vegetarian": "false",
            "delivers": "false",
            "timezone": "America/Chicago"
        }
    }
    ```
    Response:
    ```
    {
        "statusCode": 200, 
        "body": {"message": "Successfully updated test2 restaurant"}
    }
    ```
4. POST /deleteRestaurant (Auth: X-AUTH-API-KEY header)

    Body:
    ```
    {
        "record": {
            "name": "test1",
            "address": "address1"
        }
    }
    ```

    Response: 
    ```
    {
        "statusCode": 200,
        "body": {"message": "Successfully deleted abc restaurant"}
    }
    ```

### Infrastructure
* Ingress: AWS ApiGateway
* Compute: AWS Lambda
* Database: AWS Postgres DB Instance
* Encryption: HTTPS and AWS KMS
* IAC Tool: Terraform
* CI/CD Tool: Github Actions
