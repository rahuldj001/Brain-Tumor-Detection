# Client Deployment Guide

## 1. Configure the Backend URL
To make your frontend talk to your EC2 backend, you need to set the API URL.

1.  Rename `.env.example` to `.env` inside the `client` folder.
2.  Replace `<YOUR_EC2_PUBLIC_IP>` with the actual public IP address of your EC2 instance.
    ```
    REACT_APP_API_URL=http://54.123.45.67:5000
    ```

## 2. Run Locally (Development)
```bash
npm install
npm start
```

## 3. Build for Production
To create optimized static files:
```bash
npm run build
```
This will create a `build` folder. You can serve these files using Nginx on your EC2 instance or deploy them to services like AWS S3 + CloudFront, Vercel, or Netlify.
