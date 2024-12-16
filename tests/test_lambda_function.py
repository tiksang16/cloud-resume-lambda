import json
import pytest
from lambda_function.lambda_function import lambda_handler

TABLE_NAME = "visitor-counter"


@pytest.fixture
def mock_dynamodb(mocker):
    """
    Mock DynamoDB table interactions using pytest-mock.
    """
    # Mock the DynamoDB resource
    mock_dynamodb_resource = mocker.MagicMock()
    mock_table = mocker.MagicMock()

    # Mock the DynamoDB table methods
    mock_dynamodb_resource.Table.return_value = mock_table

    # Replace the `dynamodb` resource in the Lambda function with the mock
    mocker.patch("lambda_function.lambda_function.dynamodb", mock_dynamodb_resource)

    return mock_table


def test_lambda_handler_initialization(mock_dynamodb):
    """
    Test the Lambda function when the 'visitor-counter' item does not exist (initialization case).
    """
    # Simulate the case where the item does not exist in DynamoDB
    mock_dynamodb.get_item.return_value = {}

    # Simulate successful put_item call
    mock_dynamodb.put_item.return_value = {}

    # Simulate successful update_item call
    mock_dynamodb.update_item.return_value = {}

    # Mock event and context
    event = {}
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assertions
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "count" in body
    assert body["count"] == 1  # The counter should start at 1

    # Assert `put_item` was called to initialize the item
    mock_dynamodb.put_item.assert_called_once_with(
        Item={"id": "visitor-counter", "count": 0}
    )

    # Assert `update_item` was called to increment the count
    mock_dynamodb.update_item.assert_called_once()


def test_lambda_handler_increment(mock_dynamodb):
    """
    Test the Lambda function when the 'visitor-counter' item already exists.
    """
    # Simulate the case where the item exists in DynamoDB
    mock_dynamodb.get_item.return_value = {"Item": {"id": "visitor-counter", "count": 10}}

    # Simulate successful update_item call
    mock_dynamodb.update_item.return_value = {}

    # Mock event and context
    event = {}
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assertions
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "count" in body
    assert body["count"] == 11  # The counter should increment by 1

    # Assert `get_item` was called to fetch the current count
    mock_dynamodb.get_item.assert_called_once_with(Key={"id": "visitor-counter"})

    # Assert `update_item` was called to increment the count
    mock_dynamodb.update_item.assert_called_once_with(
        Key={"id": "visitor-counter"},
        UpdateExpression="set #count = :count",
        ExpressionAttributeNames={"#count": "count"},
        ExpressionAttributeValues={":count": 11},
    )


def test_lambda_handler_dynamodb_error(mock_dynamodb):
    """
    Test the Lambda function when DynamoDB raises an exception.
    """
    # Simulate an exception in the get_item call
    mock_dynamodb.get_item.side_effect = Exception("DynamoDB error")

    # Mock event and context
    event = {}
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assertions
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["message"] == "Internal Server Error"

    # Assert `get_item` was called
    mock_dynamodb.get_item.assert_called_once_with(Key={"id": "visitor-counter"})