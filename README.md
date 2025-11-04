# Geo-Smart Property Management System

A comprehensive, data-driven web application for property management, built with Django and PostGIS. This platform integrates geospatial analysis with a multi-tenant management system for property owners, tenants, and service vendors.

## Core Features

This project is built from multiple interconnected "parts" to create a single, cohesive application.

### Part 1: Property Marketplace
* **Interactive Geospatial Map:** Users can search for properties visually on a Leaflet.js map.
* **Advanced Search:** Includes a category filter and a "search within radius" feature.
* **Points of Interest (POI):** Map layers to show nearby schools, hospitals, and metro stations.

### Part 2: Automated Tenant Onboarding & Management
* **"Apply Now" System:** Tenants can apply for rental properties directly from the listing.
* **Owner Approval Workflow:** Owners can approve/reject applications, which automatically:
    * Creates a `Tenancy` record.
    * Sets the property status to "Occupied," removing it from the map.
    * Sends an email notification to the tenant.
* **Tenancy Management:** Owners can "Cancel Tenancy" to make a property available again, which also notifies the tenant.

### Part 3: Vendor & Service Marketplace
* **Multi-Role System:** Distinct dashboards and permissions for Owners, Tenants, and Vendors.
* **Job Board:** Vendors can find work on a public job board.
* **Assignment Workflow:** Owners can assign jobs to specific, approved vendors.
* **Tenant Confirmation:** A job is only marked "Completed" after the tenant confirms the work is done.

### Part 4: Community Trust & Review System
* **Property Reviews:** Past tenants can leave a 5-star rating and comment on a property after their lease ends.
* **Vendor Reviews:** Property owners can rate vendors after a maintenance job is completed.
* **Average Ratings:** The system automatically calculates and displays average ratings on property pages and in the vendor assignment list.

### Part 5: 3D Virtual Tour Editor
* **Owner-Side Management:** Owners can upload multiple 360° panoramic images ("Scenes") for a single property.
* **Hotspot Editor:** A "Manage Hotspots" page allows owners to click on the 360° image to get coordinates and create clickable links between scenes.
* **Public 3D Tour:** The property detail page displays the fully interactive, multi-scene 3D tour.

### Part 6: Financial & Analytics Hub
* **Neighborhood Insights:** A dedicated page with a map and `Chart.js` graphs that update in real-time to show average rent/sale prices for the visible map area.
* **Expense Tracking:** Owners can log all expenses (taxes, maintenance) for each of their properties.
* **CMA Tool:** A "Suggest a Market Rate" button on the "Add Property" page that analyzes comparable properties nearby to suggest an optimal price.

### Part 7: Scheduling System
* **Viewing Requests:** Tenants can request a property viewing by selecting a future date and time from a pop-up modal.
* **Owner Management:** Owners have a dedicated "Viewing Appointments" dashboard to see and "Confirm" or "Cancel" requests, which sends an email notification to the tenant.

## Tech Stack
* **Backend:** Python, Django, PostGIS
* **Frontend:** HTML, CSS, JavaScript, Bootstrap
* **Geospatial:** Leaflet.js
* **Data Visualization:** Chart.js
* **3D Tours:** Pannellum.js

## Setup & Installation

Follow these steps to run the project on your local machine.

### 1. Prerequisites
* Python 3.10+
* Git
* PostgreSQL with PostGIS extension enabled
* (On Windows) [OSGeo4W](https://www.osgeo.org/projects/osgeo4w/) (for the GDAL/GEOS libraries)

### 2. Clone the Repository
Get the code from GitHub.
```bash
git clone [https://github.com/Anand8310/Geo-Smart-Property-Management.git](https://github.com/Anand8310/Geo-Smart-Property-Management.git)
cd Geo-Smart-Property-Management

### 3. Create and Activate Virtual Environment

# Create the venv
python -m venv venv

# Activate the venv (Windows)
.\venv\Scripts\activate

# Activate the venv (Mac/Linux)
# source venv/bin/activate

### 4. install dependencies
pip install -r requirements.txt


### 5. Set Up the Database
>. Open PostgreSQL (e.g., pgAdmin) and create a new, empty database.
>. Name the database: geosmartdb
>. Enable the PostGIS extension by running this SQL query in the new database: CREATE EXTENSION postgis;

### 6. Set Up Environment Variables
>. In the root of the project, create a new file named .env
>. Copy the contents of .env.example (or the block below) into your new .env file.
>. Fill in your secret passwords. The .gitignore file will prevent this from ever being uploaded.
  .env file template:

SECRET_KEY=your-django-secret-key-goes-here
DB_PASSWORD=your-postgres-password-goes-here
EMAIL_PASSWORD=your-gmail-app-password-goes-here


###7. Run Migrations & Create Superuser

#Apply the database schema:
python manage.py migrate

#Create your admin account:
python manage.py createsuperuser


### 8. Run the Server
 #You are ready to go!
python manage.py runserver


>. The project will be live at http://127.0.0.1:8000/.

###Demo Accounts
#Superuser 
#property owner
#Tenant
#Vendor