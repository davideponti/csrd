/**
 * ── API Response Validation ─────────────────────────────────────
 * Provides runtime validation helpers for API responses using Zod-like pattern.
 * Falls back gracefully when zod is not installed.
 */

// Simple schema validator - lightweight alternative to Zod
// For production, consider installing 'zod' and replacing these with Zod schemas

export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly path: string,
    public readonly expected: string,
    public readonly received: unknown,
  ) {
    super(message)
    this.name = 'ValidationError'
  }
}

export type Schema<T> = {
  validate(data: unknown): T
  shape: Record<string, unknown>
}

/**
 * Create a simple object schema for runtime validation.
 * Example:
 *   const UserSchema = object({
 *     id: string(),
 *     email: string(),
 *     company_name: optional(string()),
 *   })
 *   const user = UserSchema.validate(responseData)
 */
export function object<T extends Record<string, Schema<any>>>(
  shape: T,
): Schema<{ [K in keyof T]: ReturnType<T[K]['validate']> }> {
  return {
    shape,
    validate(data: unknown) {
      if (typeof data !== 'object' || data === null) {
        throw new ValidationError(
          'Expected object',
          'root',
          'object',
          typeof data,
        )
      }
      const obj = data as Record<string, unknown>
      const result: Record<string, unknown> = {}

      for (const [key, schema] of Object.entries(shape)) {
        try {
          result[key] = schema.validate(obj[key])
        } catch (err) {
          if (err instanceof ValidationError) {
            throw new ValidationError(
              err.message,
              `${key}.${err.path}`,
              err.expected,
              err.received,
            )
          }
          throw err
        }
      }

      return result as any
    },
  }
}

export function string(): Schema<string> {
  return {
    shape: {},
    validate(data: unknown): string {
      if (typeof data !== 'string') {
        throw new ValidationError(
          'Expected string',
          '',
          'string',
          typeof data,
        )
      }
      return data
    },
  }
}

export function number(): Schema<number> {
  return {
    shape: {},
    validate(data: unknown): number {
      if (typeof data !== 'number' || isNaN(data)) {
        throw new ValidationError(
          'Expected number',
          '',
          'number',
          typeof data,
        )
      }
      return data
    },
  }
}

export function boolean(): Schema<boolean> {
  return {
    shape: {},
    validate(data: unknown): boolean {
      if (typeof data !== 'boolean') {
        throw new ValidationError(
          'Expected boolean',
          '',
          'boolean',
          typeof data,
        )
      }
      return data
    },
  }
}

export function optional<T>(schema: Schema<T>): Schema<T | undefined> {
  return {
    shape: {},
    validate(data: unknown): T | undefined {
      if (data === undefined || data === null) {
        return undefined
      }
      return schema.validate(data)
    },
  }
}

export function array<T>(itemSchema: Schema<T>): Schema<T[]> {
  return {
    shape: {},
    validate(data: unknown): T[] {
      if (!Array.isArray(data)) {
        throw new ValidationError(
          'Expected array',
          '',
          'array',
          typeof data,
        )
      }
      return data.map((item, index) => {
        try {
          return itemSchema.validate(item)
        } catch (err) {
          if (err instanceof ValidationError) {
            throw new ValidationError(
              err.message,
              `[${index}].${err.path}`,
              err.expected,
              err.received,
            )
          }
          throw err
        }
      })
    },
  }
}

export function uuid(): Schema<string> {
  return {
    shape: {},
    validate(data: unknown): string {
      const str = string().validate(data)
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      if (!uuidRegex.test(str)) {
        throw new ValidationError(
          'Expected valid UUID',
          '',
          'uuid',
          data,
        )
      }
      return str
    },
  }
}
