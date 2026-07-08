# CropGuard Mentor Presentation Guide

## 1. Open These Links First

Open these 5-10 minutes before the presentation so the free backend is awake.

1. Frontend: https://cropguard-plant-disease-detection.vercel.app
2. Backend API check: https://vatsal765-cropguard-plant-disease-backend.hf.space
3. GitHub repository: https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection

Expected backend response:

```text
status: running
```

If the backend is slow, wait 30-90 seconds and refresh. Hugging Face free Spaces can sleep after inactivity.

## 2. Project Introduction Line

Say this first:

```text
Good morning sir. Our project is CropGuard, an AI-based plant disease detection platform. It allows a farmer or user to register, upload or capture a crop leaf image, detect the crop disease using a trained TensorFlow model, and view scan history with confidence score and treatment-related information.
```

## 3. Tech Stack Line

```text
The frontend is built with React and Tailwind CSS. The main backend API is Django. The machine learning service uses Flask and TensorFlow/Keras. Supabase Postgres stores users, scan history, statistics, and activity data. The frontend is deployed on Vercel, and the ML backend is deployed on Hugging Face Spaces using Docker.
```

## 4. Architecture Line

```text
The user interacts with the Vercel frontend. Vercel proxies API requests to the Hugging Face backend. Django handles authentication and database records. Django sends image data to the local Flask ML service inside the same backend container. The TensorFlow model returns the leaf problem, confidence score, and advice, then Django stores the result in Supabase.
```

## 5. Live Demo Flow

Follow this order exactly.

1. Open the frontend URL.
2. Click Register.
3. Create a fresh account:

```text
First name: Mentor
Last name: Demo
Email: mentor.demo.<current-time>@gmail.com
Password: DemoPass123
Confirm password: DemoPass123
```

4. After registration, show that it redirects to Dashboard.
5. Explain the dashboard:

```text
This dashboard shows total scans, diseased plants, healthy plants, recent detections, and user activity timeline. These values come from the production Supabase database.
```

6. Click Detect Disease.
7. Upload a plant leaf image.
8. Click Analyze Image.
9. Show the result:

```text
Here the model predicts the leaf problem, confidence percentage, health status, and treatment/prevention information.
```

10. Go back to Dashboard.
11. Show that total scans and recent detection are updated.

## 6. Important Features To Mention

- Secure user registration and login.
- User-specific dashboard and scan history.
- Image upload disease detection.
- Live camera capture flow.
- TensorFlow/Keras trained model integration.
- Supabase Postgres production database.
- Permanent public frontend and backend deployment.
- Zero-cost deployment approach for student demo.

## 7. If Mentor Asks About Deployment

```text
The frontend is hosted on Vercel. The backend is a Dockerized Hugging Face Space because this project needs TensorFlow, which is heavier than normal REST APIs. Supabase is used only as the database, not as the Django backend host.
```

## 8. If Mentor Asks Why Vercel Proxy Is Used

```text
The browser must keep login cookies stable. So the React app calls the same Vercel domain, and Vercel rewrites /api requests to the Hugging Face backend. This avoids cross-domain session and CORS problems.
```

## 9. Backup Demo If Upload Is Slow

If the first scan takes time:

```text
The free ML backend can take extra time on the first request because the TensorFlow model loads into memory. After the first request, the next predictions are faster.
```

Then refresh once and try again.

## 10. Do Not Show These During Demo

- Do not show environment variables.
- Do not show Hugging Face token.
- Do not show Supabase database password.
- Do not open billing pages.

## 11. Final Closing Line

```text
So CropGuard is a complete full-stack AI project with authentication, production database, ML disease prediction, user history, and public deployment. It is ready for real mentor testing from any browser using the deployed Vercel link.
```
