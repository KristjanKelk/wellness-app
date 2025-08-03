/**
 * Utility functions for making robust fetch requests with proper error handling
 */

/**
 * Makes a fetch request with robust JSON parsing and error handling
 * @param {string} url - The URL to fetch
 * @param {object} options - Fetch options
 * @returns {Promise<object>} Parsed JSON response
 * @throws {Error} Detailed error information
 */
export async function robustFetch(url, options = {}) {
  try {
    const response = await fetch(url, options)
    
    // Handle non-OK status codes
    if (!response.ok) {
      let errorText = ''
      try {
        errorText = await response.text()
      } catch (textError) {
        console.warn('Could not read error response text:', textError)
      }
      
      console.error('API Error Response:', errorText)
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText || 'Unknown error'}`)
    }

    // Get response text
    const responseText = await response.text()
    console.log('API Response Text Length:', responseText.length)
    
    // Check if response has content
    if (!responseText || responseText.trim() === '') {
      throw new Error('Empty response from server')
    }

    // Check content type
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      console.error('Invalid content type:', contentType)
      console.error('Response text:', responseText)
      throw new Error(`Expected JSON response, got: ${contentType || 'unknown'}`)
    }

    // Parse JSON with detailed error handling
    let data
    try {
      data = JSON.parse(responseText)
    } catch (parseError) {
      console.error('JSON Parse Error:', parseError)
      console.error('Response text that failed to parse:', responseText.substring(0, 1000) + (responseText.length > 1000 ? '...' : ''))
      throw new Error(`Invalid JSON response: ${parseError.message}`)
    }

    return data
  } catch (error) {
    // Re-throw with additional context
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error(`Network error: ${error.message}`)
    }
    throw error
  }
}

/**
 * Creates a shopping list API request with authentication
 * @param {string} url - The API endpoint URL
 * @param {object} requestData - Data to send in the request body
 * @param {string} token - Authentication token
 * @returns {Promise<object>} API response data
 */
export async function makeShoppingListRequest(url, requestData, token) {
  return robustFetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(requestData)
  })
}