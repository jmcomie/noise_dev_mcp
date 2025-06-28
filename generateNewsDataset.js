#!/usr/bin/env node

const axios = require('axios');
const { faker } = require('@faker-js/faker');
const fs = require('fs-extra');
const path = require('path');

// API Configuration
const NEWS_API_KEY = '52b1342804d14ad3b935b681db50ff38';
const NEWS_API_URL = 'https://newsapi.org/v2/everything';

// Configuration
const CONFIG = {
  REAL_ARTICLES_COUNT: 40,
  FAKE_ARTICLES_COUNT: 10,
  TOPIC: process.argv[2] || 'technology', // Accept topic as command line argument
  OUTPUT_DIR: 'data',
  OUTPUT_FILE: 'mixedNewsData.json'
};

console.log('🗞️  News Dataset Generator Starting...');
console.log(`📊 Target: ${CONFIG.REAL_ARTICLES_COUNT} real + ${CONFIG.FAKE_ARTICLES_COUNT} fake articles`);
console.log(`🔍 Topic: ${CONFIG.TOPIC}`);

/**
 * Fetch real news articles from NewsAPI
 */
async function fetchRealNews() {
  console.log('\n📡 Fetching real news articles...');
  
  try {
    const response = await axios.get(NEWS_API_URL, {
      params: {
        q: CONFIG.TOPIC,
        language: 'en',
        sortBy: 'publishedAt',
        pageSize: CONFIG.REAL_ARTICLES_COUNT + 10, // Fetch extra in case some are filtered out
        apiKey: NEWS_API_KEY
      }
    });

    if (response.data.status !== 'ok') {
      throw new Error(`NewsAPI Error: ${response.data.message || 'Unknown error'}`);
    }

    const articles = response.data.articles
      .filter(article => 
        article.title && 
        article.description && 
        article.publishedAt && 
        article.url &&
        article.source?.name &&
        article.title !== '[Removed]' &&
        article.description !== '[Removed]'
      )
      .slice(0, CONFIG.REAL_ARTICLES_COUNT)
      .map(article => ({
        title: article.title,
        description: article.description,
        publishedAt: article.publishedAt,
        url: article.url,
        source: {
          name: article.source.name
        },
        sourceType: 'real'
      }));

    console.log(`✅ Successfully fetched ${articles.length} real articles`);
    return articles;

  } catch (error) {
    console.error('❌ Error fetching real news:', error.message);
    throw error;
  }
}

/**
 * Generate fake news articles using Faker.js
 */
function generateFakeNews() {
  console.log('\n🎭 Generating fake news articles...');
  
  const fakeArticles = [];
  const fakeSources = [
    'Global Truth Times',
    'NewsBlaster AI',
    'Breaking Updates 24/7',
    'World Insider Reports',
    'TruthSeeker News',
    'Daily Flash Updates',
    'Independent Voice Media',
    'Breaking Point News',
    'Instant Update Network',
    'Global News Express'
  ];

  const sensationalWords = [
    'SHOCKING', 'BREAKING', 'EXCLUSIVE', 'URGENT', 'LEAKED', 'EXPOSED',
    'UNBELIEVABLE', 'MASSIVE', 'HISTORIC', 'UNPRECEDENTED', 'SCANDAL',
    'BOMBSHELL', 'CRITICAL', 'ALARMING', 'EXPLOSIVE', 'DRAMATIC'
  ];

  const fakeTopics = [
    'Celebrity secretly controls government',
    'Scientists discover impossible technology',
    'Hidden truth about major corporation revealed',
    'Government covers up alien contact',
    'New study proves everything we know is wrong',
    'Tech billionaire\'s secret plan exposed',
    'Ancient civilization found in modern city',
    'Weather manipulation program confirmed',
    'Social media platform admits to mind control',
    'Cryptocurrency linked to foreign interference'
  ];

  for (let i = 0; i < CONFIG.FAKE_ARTICLES_COUNT; i++) {
    const sensationalWord = faker.helpers.arrayElement(sensationalWords);
    const baseTopic = faker.helpers.arrayElement(fakeTopics);
    
    const fakeArticle = {
      title: `${sensationalWord}: ${baseTopic} - You Won't Believe What Happens Next!`,
      description: `${faker.lorem.sentences(2)} This ${faker.helpers.arrayElement(['groundbreaking', 'controversial', 'shocking', 'unprecedented'])} revelation has ${faker.helpers.arrayElement(['experts', 'officials', 'insiders', 'sources'])} ${faker.helpers.arrayElement(['baffled', 'concerned', 'outraged', 'speechless'])}. ${faker.lorem.sentence()}`,
      publishedAt: faker.date.recent({ days: 7 }).toISOString(),
      url: `http://${faker.helpers.arrayElement(['fakenews247', 'truthblaster', 'breakingalerts', 'newsflash365', 'exclusivereports'])}.com/${faker.lorem.slug()}`,
      source: {
        name: faker.helpers.arrayElement(fakeSources)
      },
      sourceType: 'fake'
    };
    
    fakeArticles.push(fakeArticle);
  }

  console.log(`✅ Generated ${fakeArticles.length} fake articles`);
  return fakeArticles;
}

/**
 * Shuffle array using Fisher-Yates algorithm
 */
function shuffleArray(array) {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

/**
 * Save dataset to JSON file
 */
async function saveDataset(dataset) {
  console.log('\n💾 Saving dataset...');
  
  try {
    // Ensure data directory exists
    await fs.ensureDir(CONFIG.OUTPUT_DIR);
    
    const outputPath = path.join(CONFIG.OUTPUT_DIR, CONFIG.OUTPUT_FILE);
    
    // Add metadata
    const datasetWithMetadata = {
      metadata: {
        generated_at: new Date().toISOString(),
        total_articles: dataset.length,
        real_articles: dataset.filter(a => a.sourceType === 'real').length,
        fake_articles: dataset.filter(a => a.sourceType === 'fake').length,
        topic: CONFIG.TOPIC,
        real_percentage: Math.round((dataset.filter(a => a.sourceType === 'real').length / dataset.length) * 100),
        fake_percentage: Math.round((dataset.filter(a => a.sourceType === 'fake').length / dataset.length) * 100)
      },
      articles: dataset
    };
    
    await fs.writeJson(outputPath, datasetWithMetadata, { spaces: 2 });
    
    console.log(`✅ Dataset saved to: ${outputPath}`);
    console.log(`📈 Total articles: ${dataset.length}`);
    console.log(`📊 Real: ${datasetWithMetadata.metadata.real_articles} (${datasetWithMetadata.metadata.real_percentage}%)`);
    console.log(`🎭 Fake: ${datasetWithMetadata.metadata.fake_articles} (${datasetWithMetadata.metadata.fake_percentage}%)`);
    
    return outputPath;
    
  } catch (error) {
    console.error('❌ Error saving dataset:', error.message);
    throw error;
  }
}

/**
 * Main function
 */
async function main() {
  try {
    // Fetch real news
    const realArticles = await fetchRealNews();
    
    // Generate fake news
    const fakeArticles = generateFakeNews();
    
    // Combine datasets
    console.log('\n🔀 Combining and shuffling articles...');
    const combinedDataset = [...realArticles, ...fakeArticles];
    const shuffledDataset = shuffleArray(combinedDataset);
    
    // Save to file
    const outputPath = await saveDataset(shuffledDataset);
    
    console.log('\n🎉 News dataset generation completed successfully!');
    console.log(`📁 Output file: ${outputPath}`);
    console.log('\n💡 Usage examples:');
    console.log('  - Load in MCP server for testing');
    console.log('  - Use for ML model training/testing');
    console.log('  - Analyze fake vs real news patterns');
    
    // Sample articles preview
    console.log('\n📖 Sample articles preview:');
    shuffledDataset.slice(0, 3).forEach((article, index) => {
      console.log(`\n${index + 1}. [${article.sourceType.toUpperCase()}] ${article.title.substring(0, 80)}...`);
      console.log(`   Source: ${article.source.name}`);
      console.log(`   Published: ${new Date(article.publishedAt).toLocaleDateString()}`);
    });
    
  } catch (error) {
    console.error('\n💥 Dataset generation failed:', error.message);
    process.exit(1);
  }
}

// Handle command line help
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
🗞️  News Dataset Generator

Usage: node generateNewsDataset.js [topic]

Arguments:
  topic    News topic to fetch (default: technology)
           Examples: world, business, sports, science, health

Options:
  --help   Show this help message

Examples:
  node generateNewsDataset.js                    # Default: technology
  node generateNewsDataset.js world             # World news
  node generateNewsDataset.js "artificial intelligence"  # AI news

Output:
  - Creates data/mixedNewsData.json with 50 articles
  - 40 real articles (80%) from NewsAPI
  - 10 fake articles (20%) generated with Faker.js
  `);
  process.exit(0);
}

// Run the script
main().catch(console.error); 