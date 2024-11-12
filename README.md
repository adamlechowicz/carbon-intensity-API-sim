# carbon-intensity-API-sim

This Flask API simulates a real-time carbon intensity service based on pre-existing data. The service reads data from a CSV file where each row represents hourly carbon intensity values.

## Endpoints

### 1. Register

**Endpoint**: `/register`  
**Method**: `POST`  
**Description**: Registers a user by logging an initial timestamp, which serves as the start point for retrieving carbon intensity data. Returns a unique user identifier to be used in subsequent requests.

**Request Body**:
```json
{
  "timestamp": "2024-01-01T00:00:00"
}
```

- **timestamp**: ISO 8601 formatted string representing the initial timestamp (e.g., `YYYY-MM-DDTHH:MM:SS`).

**Response**:
- **201 Created**: 
  ```json
  {
    "user_id": "unique_user_id_hash"
  }
  ```
- **400 Bad Request**: 
  ```json
  {
    "error": "Invalid timestamp format. Use ISO format."
  }
  ```
- **400 Bad Request**: 
  ```json
  {
    "error": "Requested time not available in local carbon intensity data."
  }
  ```

**Example Request**:
```bash
curl -X POST http://localhost:6066/register -H "Content-Type: application/json" -d '{"timestamp": "2024-01-01T00:00:00"}'
```

**Example Response**:
```json
{
  "user_id": "a1b2c3d4e5f6..."
}
```

---

### 2. Get Carbon Intensity

**Endpoint**: `/get_carbon_intensity`  
**Method**: `GET`  
**Description**: Retrieves the carbon intensity for the current time based on the user's registration time. Calculates the elapsed hours since registration, then rounds down to the nearest hour and returns the corresponding carbon intensity value from the CSV data.

**Query Parameter**:
- **user_id**: The unique user ID received from the `/register` endpoint.

**Response**:
- **200 OK**:
  ```json
  {
    "timestamp": "2024-01-01T01:00:00",
    "carbon_intensity": 123.45
  }
  ```
- **404 Not Found**: If the user ID is invalid or no data is available for the calculated time.
  ```json
  {
    "error": "User ID not found. Register first."
  }
  ```

**Example Request**:
```bash
curl -X GET "http://localhost:6066/get_carbon_intensity?user_id=a1b2c3d4e5f6..."
```

**Example Response**:
```json
{
  "timestamp": "2024-01-01T01:00:00",
  "carbon_intensity": 123.45
}
```

---

## Data Source

The server loads carbon intensity data from a CSV file with the following columns:

- **timestamp**: ISO 8601 formatted datetime representing each hour (e.g., `2024-01-01T00:00:00`).
- **carbon_intensity**: Numeric value representing the carbon intensity for that hour.

Ensure the CSV file is correctly formatted and accessible by the server for the API to function as expected.

---

## Running the Server

To start the server, save the code as `carbon_intensity_server.py` and run:

```bash
python carbon_intensity_server.py
```

The server will be available at `http://localhost:6066`.

## Dependencies

- Flask
- pandas

Install dependencies using:

```bash
pip install flask pandas
```

---

## Example Usage Workflow

1. Register a user:
   ```bash
   curl -X POST http://localhost:6066/register -H "Content-Type: application/json" -d '{"timestamp": "2024-01-01T00:00:00"}'
   ```

2. Retrieve carbon intensity data using the `user_id` from registration:
   ```bash
   curl -X GET "http://localhost:6066/get_carbon_intensity?user_id=a1b2c3d4e5f6..."
   ```
```