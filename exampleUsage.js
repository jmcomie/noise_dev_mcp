#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');

/**
 * Example script showing how to load and analyze the mixed news dataset
 * Perfect for MCP server testing and integration
 */

async function loadDataset() {
  const datasetPath = path.join('data', 'mixedNewsData.json');
  
  if (!await fs.pathExists(datasetPath)) {
    console.log('❌ Dataset not found. Please run: npm run generate');
    process.exit(1);
  }
  
  const dataset = await fs.readJson(datasetPath);
  return dataset;
}

async function analyzeDataset() {
  console.log('📊 News Dataset Analyzer\n');
  
  const dataset = await loadDataset();
  const { metadata, articles } = dataset;
  
  // Basic statistics
  console.log('📈 Dataset Statistics:');
  console.log(`  Generated: ${new Date(metadata.generated_at).toLocaleString()}`);
  console.log(`  Topic: ${metadata.topic}`);
  console.log(`  Total Articles: ${metadata.total_articles}`);
  console.log(`  Real Articles: ${metadata.real_articles} (${metadata.real_percentage}%)`);
  console.log(`  Fake Articles: ${metadata.fake_articles} (${metadata.fake_percentage}%)`);
  
  // Source analysis
  const sources = {};
  const realSources = {};
  const fakeSources = {};
  
  articles.forEach(article => {
    const sourceName = article.source.name;
    sources[sourceName] = (sources[sourceName] || 0) + 1;
    
    if (article.sourceType === 'real') {
      realSources[sourceName] = (realSources[sourceName] || 0) + 1;
    } else {
      fakeSources[sourceName] = (fakeSources[sourceName] || 0) + 1;
    }
  });
  
  console.log(`\n📰 Top Real News Sources:`);
  Object.entries(realSources)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .forEach(([source, count]) => {
      console.log(`  ${source}: ${count} articles`);
    });
  
  console.log(`\n🎭 Fake News Sources:`);
  Object.entries(fakeSources).forEach(([source, count]) => {
    console.log(`  ${source}: ${count} articles`);
  });
  
  // Publication date analysis
  const now = new Date();
  const publishedDates = articles.map(a => new Date(a.publishedAt));
  const avgAge = publishedDates.reduce((sum, date) => {
    return sum + (now - date);
  }, 0) / publishedDates.length;
  
  console.log(`\n📅 Content Freshness:`);
  console.log(`  Average article age: ${Math.round(avgAge / (1000 * 60 * 60 * 24))} days`);
  
  return { dataset, metadata, articles };
}

/**
 * Classify articles (example for MCP server testing)
 */
function classifyArticles(articles) {
  console.log('\n🤖 Article Classification Examples:\n');
  
  // Show first few articles with their actual classification
  articles.slice(0, 5).forEach((article, index) => {
    const isReal = article.sourceType === 'real';
    const confidence = isReal ? '95%' : '98%'; // Mock confidence scores
    
    console.log(`${index + 1}. ${isReal ? '✅ REAL' : '❌ FAKE'} (${confidence} confidence)`);
    console.log(`   Title: "${article.title.substring(0, 80)}..."`);
    console.log(`   Source: ${article.source.name}`);
    console.log(`   Published: ${new Date(article.publishedAt).toLocaleDateString()}`);
    
    // Mock indicators that might help classify
    const indicators = [];
    if (article.title.match(/SHOCKING|BREAKING|EXCLUSIVE|URGENT|EXPOSED/i)) {
      indicators.push('Sensational language');
    }
    if (article.title.includes("You Won't Believe")) {
      indicators.push('Clickbait pattern');
    }
    if (article.url.includes('fakenews') || article.url.includes('truth')) {
      indicators.push('Suspicious domain');
    }
    if (article.source.name.includes('Global') || article.source.name.includes('Truth')) {
      indicators.push('Generic source name');
    }
    
    if (indicators.length > 0) {
      console.log(`   🚩 Indicators: ${indicators.join(', ')}`);
    }
    console.log('');
  });
}

/**
 * Filter articles by criteria
 */
function filterArticles(articles, criteria) {
  if (criteria.sourceType) {
    articles = articles.filter(a => a.sourceType === criteria.sourceType);
  }
  
  if (criteria.keyword) {
    articles = articles.filter(a => 
      a.title.toLowerCase().includes(criteria.keyword.toLowerCase()) ||
      a.description.toLowerCase().includes(criteria.keyword.toLowerCase())
    );
  }
  
  if (criteria.source) {
    articles = articles.filter(a => 
      a.source.name.toLowerCase().includes(criteria.source.toLowerCase())
    );
  }
  
  return articles;
}

/**
 * Example MCP server tool implementation
 */
const mcpTools = {
  async analyzeNews(args) {
    const { sourceType, keyword, limit = 10 } = args;
    const { articles } = await loadDataset();
    
    let filtered = filterArticles(articles, { sourceType, keyword });
    filtered = filtered.slice(0, limit);
    
    return {
      total_found: filtered.length,
      articles: filtered.map(a => ({
        title: a.title,
        source: a.source.name,
        classification: a.sourceType,
        published: a.publishedAt,
        url: a.url
      }))
    };
  },
  
  async getDatasetStats() {
    const { metadata } = await loadDataset();
    return metadata;
  },
  
  async validateArticle(args) {
    const { title, source } = args;
    const { articles } = await loadDataset();
    
    // Find similar articles
    const similar = articles.filter(a => 
      a.title.toLowerCase().includes(title.toLowerCase()) ||
      a.source.name.toLowerCase().includes(source.toLowerCase())
    );
    
    return {
      found_similar: similar.length > 0,
      similar_articles: similar.slice(0, 3),
      confidence: similar.length > 0 ? 
        (similar[0].sourceType === 'real' ? 0.85 : 0.15) : 0.5
    };
  }
};

// CLI interface
async function main() {
  try {
    const { articles } = await analyzeDataset();
    
    classifyArticles(articles);
    
    console.log('💡 Example MCP Tool Usage:\n');
    
    // Example 1: Analyze fake news
    console.log('1. Analyze fake news only:');
    const fakeNews = await mcpTools.analyzeNews({ sourceType: 'fake', limit: 3 });
    console.log(`   Found ${fakeNews.total_found} fake articles`);
    fakeNews.articles.forEach((a, i) => {
      console.log(`   ${i+1}. "${a.title.substring(0, 60)}..." - ${a.source}`);
    });
    
    console.log('\n2. Get dataset statistics:');
    const stats = await mcpTools.getDatasetStats();
    console.log(`   Topic: ${stats.topic}, Real: ${stats.real_percentage}%, Fake: ${stats.fake_percentage}%`);
    
    console.log('\n3. Validate article authenticity:');
    const validation = await mcpTools.validateArticle({ 
      title: 'SHOCKING news about technology', 
      source: 'CNN' 
    });
    console.log(`   Confidence score: ${validation.confidence}`);
    console.log(`   Found similar: ${validation.found_similar}`);
    
    console.log('\n🎯 Perfect for MCP Server Testing!');
    console.log('   - News classification models');  
    console.log('   - Source credibility analysis');
    console.log('   - Content authenticity validation');
    console.log('   - Bias detection algorithms');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Handle command line arguments
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { loadDataset, analyzeDataset, mcpTools }; 