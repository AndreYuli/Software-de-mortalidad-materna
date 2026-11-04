import { z } from 'zod';

export const registerSchema = z
  .object({
    nombre: z
      .string()
      .trim()
      .min(1, 'El nombre es obligatorio')
      .max(120, 'El nombre no puede superar 120 caracteres')
      .regex(/^[^<>]*$/, 'El nombre no puede contener los caracteres < o >'),
    email: z.string().email('Formato de correo inválido'),
    password: z
      .string()
      .min(15, 'La contraseña debe tener al menos 15 caracteres')
      .max(128, 'La contraseña no puede superar 128 caracteres'),
    confirmPassword: z.string().min(1, 'Confirma tu contraseña'),
    departamento: z.string().min(1, 'Selecciona tu departamento'),
    secretaria: z.string().min(1, 'Selecciona tu secretaría de salud'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmPassword'],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;
