# MLTC Enumerator Frontend

A modern React/Next.js frontend for the MLTC (Machine Learning Threat Context) Enumerator tool, built with **shadcn/ui** components for a professional and comprehensive user experience.

## 🎯 Overview

This frontend provides a complete workflow for ML threat analysis:

1. **System Description Input** - Users describe their ML system architecture
2. **Context Generation** - AI generates attackers, entry points, and assets
3. **Manual Editing & Review** - Users can manually add/edit/delete context items
4. **Threat Assessment** - Users provide expert ratings and comments
5. **Threat Analysis** - AI generates detailed threat chains and mitigations

## ✨ Key Features

### 🎨 Modern UI with shadcn/ui
- **Professional Design**: Consistent, accessible components following design system principles
- **Responsive Layout**: Works seamlessly across desktop, tablet, and mobile devices  
- **Dark Mode Support**: Automatic light/dark theme switching
- **Glass-morphism Design**: Modern gradient backgrounds with backdrop blur effects

### 🛡️ Complete Threat Analysis Workflow
- **Guided Input**: Rich form with examples for describing ML system architecture
- **AI-Powered Generation**: Automatic enumeration of security context from system descriptions
- **Expert Review**: Professional interface for security expert assessment and rating
- **Comprehensive Output**: Detailed threat chains with step-by-step attack paths and mitigations

### ✏️ Full CRUD Operations
- **Add Items**: Create new attackers, entry points, and assets with professional forms
- **Edit Items**: Inline editing with immediate save functionality
- **Delete Items**: Safe deletion with confirmation dialogs
- **Real-time Updates**: All changes immediately reflected in threat analysis

### 🎛️ Advanced Components

#### Attackers Management
- Description and threat characterization
- Skill level rating (1-5 Likert scale)
- Access level assessment
- Probability of attack (0.0-1.0)

#### Entry Points Management  
- Name and detailed description
- Difficulty of entry rating
- Probability of entry assessment
- Attack vector categorization

#### Assets Management
- Asset name and description
- Dynamic failure modes with tag-based management
- Value assessment and criticality rating
- Protection requirement analysis

### 📊 Expert Assessment Interface
- **Likert Scale Ratings**: Professional 1-5 scale radio button groups
- **Comment System**: Rich text comments for each assessment
- **Reviewer Tracking**: Attribution and status tracking for all reviews
- **Validation**: Comprehensive form validation ensuring complete assessments

## 🏗️ Technical Architecture

### Framework & Libraries
- **Next.js 15.3.4** - React framework with App Router
- **TypeScript** - Full type safety aligned with backend schemas
- **shadcn/ui** - Professional component library built on Radix UI
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful, consistent icons

### Component Structure
```
app/
├── components/
│   ├── DFDInput.tsx          # System description input form
│   ├── ContextEditor.tsx     # Manual CRUD for context items
│   ├── LikertScale.tsx       # 1-5 rating scale component
│   └── (other components)
├── types.ts                  # TypeScript definitions aligned with backend
├── services/
│   └── api.ts               # Backend API integration
└── page.tsx                 # Main application orchestration
```

### Type Safety & Schema Alignment
All TypeScript interfaces precisely match the backend Pydantic schemas:

```typescript
// Core entities
interface Attacker {
  id: string;
  description: string;
  skill_level: Likert;
  access_level: Likert;  
  prob_of_attack: number;
}

interface EntryPoint {
  id: string;
  name: string;
  description: string;
  prob_of_entry: number;
  difficulty_of_entry: Likert;
}

interface Asset {
  id: string;
  name: string;
  description: string;
  failure_modes: string[];
}
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ OR Docker
- npm or pnpm package manager (if running without Docker)

### Installation & Development

#### Option 1: Local Development (Node.js)

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:3000
```

#### Option 2: Docker Development

```bash
# Quick start with the development script
./start-dev.sh

# Or manually with Docker Compose
docker-compose -f docker-compose.dev.yml up --build

# Open browser to http://localhost:3000
```

### Build for Production

#### Option 1: Local Build

```bash
# Create optimized production build
npm run build

# Start production server  
npm start
```

#### Option 2: Docker Production Build

```bash
# Build production image
docker build -t mltc-frontend .

# Run production container
docker run -p 3000:3000 mltc-frontend
```

## 🔌 Backend Integration

The frontend integrates with the Python FastAPI backend through REST endpoints:

### API Endpoints
- `POST /context` - Generate initial context from system description
- `POST /generate` - Generate threat analysis from verified context
- `GET /ping` - Health check endpoint

### Request/Response Flow
1. **Context Request** → System description sent to `/context`
2. **Context Response** → AI-generated attackers, entry points, assets
3. **User Review** → Manual editing and expert assessment
4. **Threat Request** → Verified context sent to `/generate`  
5. **Threat Response** → Detailed threat chains and mitigations

## 🎨 Design System

### Color Palette
- **Primary**: Blue gradient (blue-600 to indigo-600)
- **Success**: Green tones for completed actions
- **Warning**: Amber/orange for cautions
- **Destructive**: Red tones for deletions and threats
- **Muted**: Gray tones for secondary content

### Typography
- **Headings**: Bold, clear hierarchy with proper spacing
- **Body**: Readable text with good contrast ratios
- **Code**: Monospace font for technical content

### Components
- **Cards**: Elevated surfaces with subtle shadows
- **Buttons**: Multiple variants (default, outline, destructive, ghost)
- **Forms**: Professional inputs with proper labeling and validation
- **Navigation**: Clear visual hierarchy and state indication

## 📱 Responsive Design

The application is fully responsive across all device sizes:

- **Desktop** (1200px+): Full multi-column layouts with side-by-side content
- **Tablet** (768px-1199px): Responsive grids that stack appropriately  
- **Mobile** (320px-767px): Single-column layouts optimized for touch

## ♿ Accessibility Features

- **Keyboard Navigation**: Full keyboard support for all interactive elements
- **Screen Readers**: Proper ARIA labels and semantic HTML structure
- **High Contrast**: Excellent color contrast ratios for all text
- **Focus Management**: Clear focus indicators and logical tab order

## 🔮 Future Enhancements

### Phase 2 Features
- **Export Functionality**: PDF/CSV export of threat analysis reports
- **Advanced Search**: Filter and search across context items and threats
- **Collaboration**: Multi-user review workflows with conflict resolution
- **Templates**: Pre-built context templates for common ML architectures

### Phase 3 Features  
- **Integration**: Connect with external threat intelligence feeds
- **Automation**: Automated threat monitoring and alert systems
- **Analytics**: Dashboard with threat trend analysis and metrics
- **API**: Public API for integration with security tools

## 🧪 Testing

The application includes comprehensive testing:

```bash
# Run unit tests
npm test

# Run E2E tests  
npm run test:e2e

# Run type checking
npm run type-check
```

## 🐳 Docker Setup

The frontend includes optimized Docker configurations for both development and production:

### Docker Files

- **`Dockerfile`** - Multi-stage production build with optimized image size
- **`Dockerfile.dev`** - Development environment with hot reloading
- **`docker-compose.dev.yml`** - Development compose configuration
- **`.dockerignore`** - Optimized build context exclusions

### Development with Docker

```bash
# Quick start (recommended)
./start-dev.sh

# Manual Docker Compose
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop containers
docker-compose -f docker-compose.dev.yml down
```

### Production Docker Build

```bash
# Build optimized production image
docker build -t mltc-frontend:latest .

# Run production container
docker run -d \
  --name mltc-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-backend-url \
  mltc-frontend:latest

# Check container status
docker ps

# View logs
docker logs mltc-frontend
```

### Docker Features

- **Multi-stage builds** for optimized production images
- **Volume mounting** for development hot reloading
- **Environment variable** support for API configuration
- **Security** with non-root user in production
- **Caching** optimized Docker layer caching
- **Standalone output** for minimal runtime dependencies

## 📦 Deployment

### Vercel (Recommended)
```bash
# Deploy to Vercel
vercel --prod
```

### Docker Production
```bash
# Build and tag for deployment
docker build -t mltc-frontend:v1.0.0 .

# Push to registry (replace with your registry)
docker push your-registry/mltc-frontend:v1.0.0
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- **shadcn/ui** for the excellent component library
- **Radix UI** for accessible primitive components  
- **Tailwind CSS** for the utility-first CSS framework
- **Lucide** for the beautiful icon library
