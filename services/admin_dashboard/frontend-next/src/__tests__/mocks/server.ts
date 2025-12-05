/**
 * MSW Server Setup for Node.js environment (Vitest)
 * 
 * This sets up the mock server for unit tests.
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create the mock server with default handlers
export const server = setupServer(...handlers);

// Export utilities for modifying handlers in tests
export { handlers };

