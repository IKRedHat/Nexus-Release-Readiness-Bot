# Nexus Admin Dashboard - Next.js 14

Modern, high-performance admin dashboard built with Next.js 14 and optimized for Vercel deployment.

## Features

- ✅ Next.js 14 with App Router
- ✅ TypeScript (Vercel-compatible, zero build issues)
- ✅ Tailwind CSS with custom theme
- ✅ Responsive design
- ✅ Authentication (SSO + Local)
- ✅ Dashboard with real-time stats
- ✅ Release management
- ✅ Health monitoring
- ✅ Feature requests
- ✅ User & Role management (RBAC)

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Deployment to Vercel

1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL`: Your backend API URL
4. Deploy

That's it! Vercel automatically detects Next.js and configures everything.

## Project Structure

```
src/
├── app/           # Next.js App Router pages
├── components/    # React components
├── lib/           # Utilities and API client
├── hooks/         # Custom React hooks
├── providers/     # Context providers
├── types/         # TypeScript types
└── styles/        # Global styles
```

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-api-url.com
NEXT_PUBLIC_APP_VERSION=3.0.0
```

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Date Utils**: date-fns

## License

MIT

## ✅ Commit Author Verified

This commit tests that the GitHub email verification is working correctly.
Vercel should now auto-deploy without 'commit author required' errors.
