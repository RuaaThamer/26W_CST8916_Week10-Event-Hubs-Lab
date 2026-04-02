# Assignment 2: Real-time Stream Analytics Pipeline
**Course:** CST8916 – Remote Data and Real-time Applications  
**Student Name:** Ruaa Thamer  
**Video Demo:** [https://youtu.be/43UjQj-eMxM](https://youtu.be/43UjQj-eMxM)

## 1. Overview
This project extends a standard clickstream pipeline by adding an analytics layer using Azure Stream Analytics. The system captures user interactions from a web store, enriches the data with device metadata, processes it in real-time to identify traffic patterns and spikes, and displays the results on a live dashboard.

## 2. Architecture Diagram
The following diagram illustrates the flow of data from the client-side store to the live analytics dashboard.

![Architecture Diagram](https://github.com/user-attachments/assets/dc32f2b3-f200-467c-be23-18cd52710813)

## 3. Design Decisions

### Event Enrichment Strategy (Part 1)
I decided to implement the enrichment of event data directly on the client-side using JavaScript within the browser. The primary reason for this choice is efficiency; the browser natively possesses all the necessary metadata regarding the user's environment—such as `deviceType`, `browser`, and `os`—through the `navigator` object. By capturing this information at the source, I ensured that every click event arriving at the Azure Event Hub was already "smart" and fully populated with the required fields. This approach eliminates the need for expensive server-side processing or secondary lookup steps later in the pipeline, ensuring the data is ready for immediate analysis as soon as it is ingested.

### Stream Analytics to Dashboard Integration (Part 2)
To connect the processing layer to the user interface, I utilized an Azure Function to serve as a real-time bridge between Azure Stream Analytics and the web dashboard. While Azure Stream Analytics is exceptionally powerful at aggregating data streams, it lacks the capability to communicate directly with a static HTML frontend. By using an Azure Function as a middleman, I created a seamless data flow where every time a Stream Analytics "Window" (such as a 10-second count) completes, the results are automatically pushed to the Function. The Function then broadcasts this data to the dashboard, allowing the charts to update dynamically in real-time without requiring any manual page refreshes from the user.

## 4. Setup Instructions

### Azure Resources Needed
* **Azure App Service:** To host the Store frontend and the Analytics Dashboard.
* **Azure Event Hubs:** To act as the ingestion point for clickstream data.
* **Azure Stream Analytics:** To process the stream and perform windowed aggregations.
* **Azure Function App:** To receive processed data and update the dashboard.

### Environment Variables & Configuration
Ensure the following settings are configured in your Azure environment:
* `EVENT_HUB_CONNECTION_STRING`: The connection string for the Clickstream namespace.
* `EVENT_HUB_NAME`: The specific Hub name (e.g., `clickstream`).
* `SAQL_INPUT`: `clickstream`
* `SAQL_OUTPUT`: `mystore` (The Azure Function alias).

### How to Run
1. Deploy the code to **Azure App Service**.
2. Start the **Azure Stream Analytics** job (`Ruaa-Click-Counter`).
3. Open the Store URL and generate events by clicking on products.
4. Open the Dashboard URL to view real-time breakdown of device types and traffic spikes.

---
*AI Disclosure: I used Gemini/AI assistance to help draft the architecture diagram logic and refine the documentation structure. All code and Azure configurations were verified and tested manually.*
