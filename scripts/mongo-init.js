// MongoDB initialization script
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'project_db');

// Function to create collection if it doesn't exist
function createCollectionIfNotExists(collectionName) {
  const collections = db.getCollectionNames();
  if (!collections.includes(collectionName)) {
    print(`Creating collection: ${collectionName}`);
    db.createCollection(collectionName);
    return true;
  }
  print(`Collection ${collectionName} already exists`);
  return false;
}

// Function to create index if it doesn't exist
function createIndexIfNotExists(collection, indexSpec, options = {}) {
  const indexName = Object.keys(indexSpec).map(key => `${key}_${indexSpec[key]}`).join('_');
  const indexes = db[collection].getIndexes();
  const exists = indexes.some(idx => idx.name === indexName);
  
  if (!exists) {
    print(`Creating index on ${collection}: ${JSON.stringify(indexSpec)}`);
    db[collection].createIndex(indexSpec, options);
    return true;
  }
  print(`Index ${indexName} already exists on ${collection}`);
  return false;
}

// Initialize database - create collections
createCollectionIfNotExists('api_keys');
createCollectionIfNotExists('projects');
createCollectionIfNotExists('documents');
createCollectionIfNotExists('conversations');

// OAuth 2.0 related collections
createCollectionIfNotExists('oauth_clients');
createCollectionIfNotExists('oauth_tokens');
createCollectionIfNotExists('users');

// Create indexes
createIndexIfNotExists('api_keys', { "key": 1 }, { unique: true });
createIndexIfNotExists('projects', { "project_id": 1 }, { unique: true });
createIndexIfNotExists('documents', { "project_id": 1 });
createIndexIfNotExists('documents', { "project_id": 1, "document_type": 1 });
createIndexIfNotExists('conversations', { "project_id": 1, "timestamp": 1 });

// OAuth 2.0 related indexes
createIndexIfNotExists('oauth_clients', { "client_id": 1 }, { unique: true });
createIndexIfNotExists('oauth_tokens', { "access_token": 1 }, { unique: true });
createIndexIfNotExists('oauth_tokens', { "refresh_token": 1 }, { unique: true, sparse: true });
createIndexIfNotExists('users', { "username": 1 }, { unique: true });
createIndexIfNotExists('users', { "email": 1 }, { unique: true });

// Insert default OAuth client if specified in environment and doesn't exist
const apiKey = process.env.API_KEY;
if (apiKey) {
  const existingClient = db.oauth_clients.findOne({ client_id: "default-client" });
  if (!existingClient) {
    print("Inserting default OAuth client");
    db.oauth_clients.insertOne({
      client_id: "default-client",
      client_secret: apiKey,
      client_name: "Default Client",
      client_uri: "http://localhost:5000",
      redirect_uris: ["http://localhost:5000/oauth/callback"],
      grant_types: ["authorization_code", "refresh_token", "client_credentials"],
      response_types: ["code", "token"],
      scope: "read write",
      created_at: new Date(),
      updated_at: new Date()
    });
    
    // Create a default admin user
    db.users.insertOne({
      username: "admin",
      email: "admin@example.com",
      password: apiKey, // In production, this should be properly hashed
      is_active: true,
      is_admin: true,
      created_at: new Date(),
      updated_at: new Date()
    });
  } else {
    print("Default OAuth client already exists");
  }
}

// Schema examples for reference - not inserted into the database
const schemas = {
  project: {
    project_id: "unique-id",
    name: "Project Name",
    description: "Project description",
    created_at: new Date(),
    updated_at: new Date(),
    status: "active"
  },
  
  document: {
    project_id: "unique-id",
    document_type: "ideation", // or "business_case", "charter", "technical", etc.
    content: "Document content",
    created_at: new Date(),
    updated_at: new Date()
  },
  
  conversation: {
    project_id: "unique-id",
    timestamp: new Date(),
    user: "User ID",
    message: "Message content",
    metadata: {
      reference_id: "optional-reference-id"
    }
  },
  
  // OAuth 2.0 related schemas
  oauth_client: {
    client_id: "client-id",
    client_secret: "client-secret",
    client_name: "Client Name",
    client_uri: "https://client.example.com",
    redirect_uris: ["https://client.example.com/callback"],
    grant_types: ["authorization_code", "refresh_token", "client_credentials"],
    response_types: ["code", "token"],
    scope: "read write",
    created_at: new Date(),
    updated_at: new Date()
  },
  
  oauth_token: {
    access_token: "access-token",
    refresh_token: "refresh-token",
    client_id: "client-id",
    user_id: "user-id", // Optional, not present for client credentials
    scope: "read write",
    issued_at: new Date(),
    expires_at: new Date(),
    token_type: "Bearer"
  },
  
  user: {
    username: "username",
    email: "user@example.com",
    password: "hashed-password",
    is_active: true,
    is_admin: false,
    created_at: new Date(),
    updated_at: new Date()
  }
};

print("MongoDB initialization completed"); 