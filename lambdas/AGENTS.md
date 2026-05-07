# System Agents and Interactions

This document outlines the key "agents" or entities within the system and their interactions, with a particular focus on the workflow for updating a volunteer's profile picture.

## Key Agents

1.  **Client (Frontend)**:
    *   The user interface (web, mobile app, etc.) that initiates requests and interacts with the user.
    *   Responsible for:
        *   Making API requests to the Application Backend.
        *   Handling user input and displaying responses.
        *   Directly uploading files to Supabase Storage (S3) using presigned URLs.
        *   Managing JWT tokens for authentication.

2.  **Application Backend (FastAPI)**:
    *   The core API server built with FastAPI.
    *   Responsible for:
        *   Processing API requests, routing them to appropriate controllers and use cases.
        *   Implementing business logic (e.g., creating volunteers, managing applications, generating presigned URLs).
        *   Interacting with the database (via SQLAlchemy ORM).
        *   Authenticating and authorizing requests using JWTs (from Supabase) and checking user roles (e.g., admin).
        *   Generating public URLs for stored assets.

3.  **Supabase Storage (S3-compatible)**:
    *   The object storage service used for storing files like profile pictures.
    *   Accessed via presigned URLs for direct uploads and public URLs for retrieval.
    *   Managed by the Supabase platform, but functionally equivalent to an S3 bucket in this context.

## 1. All Application Routes Overview

**Main Router (`controllers/appRouter.py`):**
*   `GET /`: Basic HTML response.
*   Includes the following sub-routers:
    *   `volunteersRouter` (for volunteer-related operations)
    *   `incidentTicketsRouter` (for incident ticket operations)
    *   `adminRouter` (for admin-specific operations)
    *   `alliedOfficeRouter` (for allied office operations)

**Volunteer Routes (`controllers/volunteerController.py`):**
*   `GET /volunteers`
    *   **Response Schema:** `List[VolunteerResponseDto]`
    *   Retrieves a list of all volunteers.
*   `GET /volunteers/{volunteer_id}`
    *   **Response Schema:** `VolunteerResponseDto`
    *   Retrieves a specific volunteer's profile by ID.
*   `PATCH /volunteers/{volunteer_id}`
    *   **Request Schema:** `VolunteerUpdateDto`
    *   **Response Schema:** `VolunteerResponseDto`
    *   Updates a volunteer's profile. **Requires authentication.**
*   `GET /volunteers/profile-image-upload-url`
    *   **Response Schema:** `Dict[str, str]` (e.g., `{"upload_url": "...", "key": "..."}`)
    *   Generates a presigned URL for direct image upload to storage. **No authentication required to request the URL.**
*   `POST /volunteer-applications`
    *   **Request Schema:** `VolunteerApplicationCreateDto`
    *   **Response Schema:** `VolunteerApplicationResponseDto`
    *   Creates a new volunteer application.
*   `GET /volunteer-applications`
    *   **Response Schema:** `List[VolunteerApplicationResponseDto]`
    *   Retrieves all volunteer applications (intended for admin review).
*   `PUT /volunteer-applications/{application_id}/approve`
    *   **Response Schema:** `VolunteerApplicationResponseDto`
    *   Approves a volunteer application. **Requires admin authentication.**
*   `PUT /volunteer-applications/{application_id}/reject`
    *   **Response Schema:** `VolunteerApplicationResponseDto`
    *   Rejects a volunteer application. **Requires admin authentication.**

**Incident Ticket Routes (`controllers/incidentTicketController.py`):**
*   `POST /incidents`
    *   Creates a new incident ticket.
*   `GET /incidents/pending`
    *   Retrieves pending incident tickets.
*   `GET /incidents/requested`
    *   Retrieves requested incident tickets.
*   `POST /incidents/{public_case_id}/claim`
    *   Claims an incident ticket.
*   `GET /incidents/{public_case_id}`
    *   Retrieves a specific incident ticket by public case ID.
*   `PATCH /incidents/{public_case_id}/status`
    *   Updates the status of an incident ticket.
*   `GET /incidents/{public_case_id}/logs`
    *   Retrieves status logs for an incident ticket.
*   `GET /volunteers/notifications`
    *   Retrieves notifications for volunteers.

**Admin Routes (`controllers/adminController.py`):**
*   `GET /admin/tickets`
    *   **Response Schema:** `List[IncidentTicketResponseDto]`
    *   Retrieves incident tickets for administration. **Requires admin authentication.**
*   `GET /admin/tickets/{ticket_status}`
    *   **Response Schema:** `List[IncidentTicketResponseDto]`
    *   Retrieves incident tickets by status for administration. **Requires admin authentication.**
*   `GET /admin/notifications/{admin_id}`
    *   **Response Schema:** `List[NotificationResponseDto]`
    *   Retrieves notifications for a specific admin. **Requires admin authentication.**
*   `GET /admin/admins`
    *   **Response Schema:** `List[AdminResponseDto]`
    *   Retrieves a list of all admins. **Requires admin authentication.**
*   `POST /admin`
    *   **Request Schema:** (Admin creation DTO - not explicitly shown in current context but implied)
    *   **Response Schema:** `AdminResponseDto`
    *   Creates a new admin user. **Requires admin authentication.**

**Allied Office Routes (`controllers/alliedOfficeController.py`):**
*   `GET /offices`
    *   **Response Schema:** `List[AlliedOfficeResponseDto]`
    *   Retrieves a list of all allied offices.
*   `GET /offices/{office_id}`
    *   **Response Schema:** `AlliedOfficeResponseDto`
    *   Retrieves a specific allied office by ID.

## 2. Workflow for Updating a Volunteer Profile Picture

The process for updating a volunteer's profile picture is a three-step workflow involving direct interaction with the storage service (Supabase Storage, acting as S3) and the application's API:

### Step 1: Client Requests Presigned Upload URL

*   **Initiator:** Client (Frontend)
*   **Action:** Sends an HTTP `GET` request to `/volunteers/profile-image-upload-url`.
*   **Authorization:** **No `Authorization` header is required for this API call.** This endpoint is designed to allow any client to request an upload URL.
*   **Server Response (`Dict[str, str]`):** The server responds with a JSON object containing:
    *   `upload_url`: A temporary, authenticated URL for direct upload to Supabase Storage (S3).
    *   `key`: The unique identifier for the image object within Supabase Storage (e.g., `profiles/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jpg`).
    ```json
    {
        "upload_url": "https://<your-bucket-name>.supabase.co/storage/v1/object/sign/profiles/xxxxxxxx.jpg?token=...",
        "key": "profiles/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jpg"
    }
    ```

### Step 2: Client Uploads Image Directly to Supabase Storage

*   **Initiator:** Client (Frontend)
*   **Action:** Performs an HTTP `PUT` request, with the image file as the body.
*   **Target:** Supabase Storage (S3) – directly to the `upload_url` obtained in Step 1.
*   **Authorization:** The `upload_url` itself contains temporary credentials, authorizing the client to `PUT` the file to that specific location. **No separate `Authorization` header is sent to the Application Backend during this step.**
*   **Server Response (from Storage Service):** A successful upload typically returns a `200 OK` status from the storage service.

### Step 3: Client Informs Backend of Uploaded Image (Profile Update)

*   **Initiator:** Client (Frontend)
*   **Action:** Sends an HTTP `PATCH` request to `/volunteers/{volunteer_id}`. The request body includes a `profile_image_key` field with the `key` obtained in Step 1.
*   **Target:** Application Backend
*   **Authorization:** An `Authorization` header with a valid Supabase JWT (JSON Web Token) is **required**. The token must be in the format `Bearer <YOUR_JWT_TOKEN>`. The JWT is verified by `get_current_user_id` (from `utils/auth.py`), which checks the token's `sub` claim. The `sub` claim in the JWT **must match** the `volunteer_id` in the URL path to ensure the user is updating their own profile.
*   **Request Body (`VolunteerUpdateDto`) Example:**
    ```json
    {
        "profile_image_key": "profiles/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jpg"
    }
    ```
*   **Server Response (`VolunteerResponseDto`):** The application backend updates the volunteer's record in the database with the new `profile_image_key`. The response will be the updated `VolunteerResponseDto`, which now includes the `profile_image_key` and a publicly accessible `profile_image_url`.

This structured workflow ensures efficient handling of large image uploads directly to cloud storage, while maintaining proper authentication and authorization for associating the image with a user's profile within the application.
