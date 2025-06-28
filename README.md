# 🗞️ News Dataset Generator

A Node.js script that generates a mixed dataset of **80% real news** and **20% fake news** for testing MCP servers and machine learning models.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Generate dataset with default topic (technology)
npm run generate

# Or run directly with custom topic
node generateNewsDataset.js "artificial intelligence"
```

## 📊 Features

- **Real News (80%)**: Fetches 40 live articles from NewsAPI.org
- **Fake News (20%)**: Generates 10 realistic fake articles using Faker.js
- **Shuffled Output**: Randomly mixed dataset for unbiased testing
- **Rich Metadata**: Includes generation stats and article details
- **Customizable Topics**: Supports any news topic/keyword

## 🔧 Configuration

### API Keys
- **NewsAPI**: `52b1342804d14ad3b935b681db50ff38` (already configured)
- **Mediastack**: `ca91d76b933a17c6d2380dec16f12459` (available for future use)

### Output Structure
Each article contains:
```typescript
{
  title: string,
  description: string,
  publishedAt: string,
  url: string,
  source: {
    name: string
  },
  sourceType: "real" | "fake"
}
```

## 📁 Output Format

The script generates `data/mixedNewsData.json` with:

```json
{
  "metadata": {
    "generated_at": "2024-06-28T20:30:00.000Z",
    "total_articles": 50,
    "real_articles": 40,
    "fake_articles": 10,
    "topic": "technology",
    "real_percentage": 80,
    "fake_percentage": 20
  },
  "articles": [
    {
      "title": "Tech Company Announces Breakthrough AI",
      "description": "Revolutionary development in artificial intelligence...",
      "publishedAt": "2024-06-28T15:30:00Z",
      "url": "https://techcrunch.com/2024/06/28/ai-breakthrough",
      "source": { "name": "TechCrunch" },
      "sourceType": "real"
    },
    {
      "title": "SHOCKING: Scientists discover impossible technology - You Won't Believe What Happens Next!",
      "description": "Lorem ipsum dolor sit amet...",
      "publishedAt": "2024-06-27T10:15:00Z",
      "url": "http://fakenews247.com/impossible-tech",
      "source": { "name": "Global Truth Times" },
      "sourceType": "fake"
    }
  ]
}
```

## 🎯 Usage Examples

### Basic Usage
```bash
# Technology news (default)
node generateNewsDataset.js

# World news
node generateNewsDataset.js world

# Business news
node generateNewsDataset.js business

# Multi-word topics
node generateNewsDataset.js "climate change"
```

### Available Topics
- `technology` (default)
- `world`
- `business`
- `sports`
- `science`
- `health`
- `entertainment`
- `politics`
- Custom keywords/phrases

## 🧪 Testing Features

### Real News Sources
- Live articles from NewsAPI.org
- Verified publishers (CNN, BBC, Reuters, etc.)
- Recent articles (sorted by publish date)
- Filtered for quality (removes [Removed] content)

### Fake News Generation
- Sensational headlines with clickbait patterns
- Fake but realistic-looking URLs
- Made-up news sources:
  - "Global Truth Times"
  - "NewsBlaster AI"
  - "Breaking Updates 24/7"
  - And more...
- Recent fake publish dates
- Vague, biased descriptions

## 🔍 MCP Server Integration

Perfect for testing MCP servers that need to:
- Classify news as real vs fake
- Analyze article sentiment
- Extract key information
- Train ML models on mixed datasets

### Sample MCP Tools
```javascript
// Example tool to analyze dataset
{
  name: "analyze_news_dataset",
  description: "Analyze the mixed news dataset",
  inputSchema: {
    type: "object",
    properties: {
      dataset_path: { type: "string" }
    }
  }
}
```

## 📈 Quality Metrics

- **Real Articles**: 40 (80%)
  - Sourced from verified publishers
  - Recent publication dates
  - Complete metadata

- **Fake Articles**: 10 (20%)
  - Sensationalized titles
  - Fake domains and sources
  - Realistic but fabricated content

## 🛠️ Dependencies

```json
{
  "axios": "^1.6.2",
  "@faker-js/faker": "^8.3.1",
  "fs-extra": "^11.2.0"
}
```

## 🚨 Disclaimer

This tool is designed for:
- ✅ Educational purposes
- ✅ Testing ML models
- ✅ MCP server development
- ✅ Research projects

**Not for**:
- ❌ Spreading misinformation
- ❌ Production news services
- ❌ Deceiving users

## 📝 License

MIT License - Use responsibly for testing and educational purposes.

---

Generated with ❤️ for MCP server testing 