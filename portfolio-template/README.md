# Portfolio Template

A data-driven developer portfolio built with Next.js, Tailwind CSS, and Framer Motion. All personal content is controlled from a single config file.

## Quick Start

```bash
cd portfolio-template
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Customization

Edit **`src/config/portfolio.ts`** to replace the placeholder data with your own information. This is the only file you need to change. It controls:

- Name, title, bio, and contact info
- Social media links
- About section with highlights
- Skills (grouped by category)
- Projects with descriptions, tech tags, and links
- Work experience timeline

## Adding Images

Place your images in the `public/` directory and reference them by path in the config file (e.g. `"/my-project.jpg"`).

## Deployment

This is a standard Next.js app. Deploy with one click on [Vercel](https://vercel.com/new) or build for production:

```bash
npm run build
npm start
```
