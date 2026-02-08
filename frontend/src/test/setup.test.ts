// Basic setup test
describe('Test Infrastructure', () => {
  test('should be able to run tests', () => {
    expect(1 + 1).toBe(2)
  })

  test('should have access to testing utilities', () => {
    expect(jest).toBeDefined()
    expect(global.localStorage).toBeDefined()
    expect(window.matchMedia).toBeDefined()
  })
})