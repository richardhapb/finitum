import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { categoriesApi, expensesApi } from '../../lib/api';
import type { Category } from '../../types/models';

const expenseSchema = z.object({
  commerce: z.string().min(1, 'El comercio es obligatorio'),
  amount: z.coerce.number().positive('El monto debe ser positivo'),
  currency: z.string().min(1, 'La moneda es obligatoria'),
  category_id: z.coerce.number().int().positive('La categoria es obligatoria'),
  description: z.string().optional(),
  date: z.string().optional(),
});

type ExpenseFormData = z.infer<typeof expenseSchema>;

export function ExpenseForm() {
  const queryClient = useQueryClient();
  const [showCategoryCreator, setShowCategoryCreator] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryPattern, setNewCategoryPattern] = useState('');

  const { data: categories = [], isLoading: isLoadingCategories, error: categoriesError } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.getAll,
  });

  const {
    register,
    handleSubmit,
    getValues,
    reset,
    setValue,
    formState: { errors },
  } = useForm<ExpenseFormData>({
    resolver: zodResolver(expenseSchema) as any,
    defaultValues: {
      currency: 'clp',
      date: new Date().toISOString().split('T')[0],
    },
  });

  const generalCategory = categories.find((category) => category.slug === 'general');

  useEffect(() => {
    if (!generalCategory) {
      return;
    }

    const currentCategoryId = getValues('category_id');
    if (!currentCategoryId) {
      setValue('category_id', generalCategory.id);
    }
  }, [generalCategory, getValues, setValue]);

  const createExpenseMutation = useMutation({
    mutationFn: expensesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      reset({
        currency: 'clp',
        category_id: generalCategory?.id,
        date: new Date().toISOString().split('T')[0],
        commerce: '',
        amount: undefined,
        description: '',
      });
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      let message = 'No se pudo agregar el gasto';
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
      }
      alert(message);
    },
  });

  const createCategoryMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: (category) => {
      queryClient.setQueryData<Category[]>(['categories'], (currentCategories = []) => {
        const nextCategories = [...currentCategories, category];
        return nextCategories.sort((left, right) => left.name.localeCompare(right.name, 'es-CL'));
      });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setValue('category_id', category.id);
      setNewCategoryName('');
      setNewCategoryPattern('');
      setShowCategoryCreator(false);
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'No se pudo crear la categoria');
    },
  });

  const onSubmit = (data: ExpenseFormData) => {
    createExpenseMutation.mutate(data);
  };

  const handleCreateCategory = () => {
    if (!newCategoryName.trim()) {
      alert('Ingresa un nombre para la categoria');
      return;
    }

    createCategoryMutation.mutate({
      name: newCategoryName,
      pattern: newCategoryPattern.trim() || undefined,
    });
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
      <h2 className="text-xl font-bold mb-4 text-white">Agregar gasto</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">Comercio</label>
            <input
              {...register('commerce')}
              type="text"
              placeholder="Ej: Starbucks"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
            />
            {errors.commerce && (
              <p className="text-red-400 text-sm mt-1">{errors.commerce.message}</p>
            )}
          </div>

          <div>
            <div className="mb-1 flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center">
              <label className="block text-sm font-medium text-gray-200">Categoria</label>
              <button
                type="button"
                onClick={() => setShowCategoryCreator((value) => !value)}
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                {showCategoryCreator ? 'Cancelar' : 'Nueva categoria'}
              </button>
            </div>
            <select
              {...register('category_id')}
              disabled={isLoadingCategories || createExpenseMutation.isPending}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-750"
            >
              <option value="">
                {isLoadingCategories ? 'Cargando categorias...' : 'Selecciona una categoria'}
              </option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
            {showCategoryCreator && (
              <div className="mt-3 space-y-2">
                <input
                  value={newCategoryName}
                  onChange={(event) => setNewCategoryName(event.target.value)}
                  type="text"
                  placeholder="Nombre de tu categoria"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
                />
                <div className="space-y-2">
                  <label className="block text-xs font-medium text-gray-300">
                    Palabra clave para categorizar automaticamente
                  </label>
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <input
                      value={newCategoryPattern}
                      onChange={(event) => setNewCategoryPattern(event.target.value)}
                      type="text"
                      placeholder="Ej: JUMBO o PETSHOP"
                      className="min-w-0 flex-1 px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
                    />
                    <button
                      type="button"
                      onClick={handleCreateCategory}
                      disabled={createCategoryMutation.isPending}
                      className="w-full shrink-0 px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors sm:w-auto"
                    >
                      {createCategoryMutation.isPending ? 'Creando...' : 'Crear'}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-400">
                  Si defines una palabra clave, los gastos importados que la contengan usaran esta categoria.
                </p>
              </div>
            )}
            {categoriesError && (
              <p className="text-red-400 text-sm mt-1">
                No se pudieron cargar las categorias.
              </p>
            )}
            {errors.category_id && (
              <p className="text-red-400 text-sm mt-1">{errors.category_id.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-200">Monto</label>
              <input
                {...register('amount')}
                type="number"
                step="0.01"
                placeholder="0.00"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
              />
              {errors.amount && (
                <p className="text-red-400 text-sm mt-1">{errors.amount.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-200">Moneda</label>
              <select
                {...register('currency')}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="clp">CLP</option>
                <option value="usd">USD</option>
              </select>
              {errors.currency && (
                <p className="text-red-400 text-sm mt-1">{errors.currency.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">Fecha</label>
            <input
              {...register('date')}
              type="date"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.date && (
              <p className="text-red-400 text-sm mt-1">{errors.date.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-200">
              Descripcion (opcional)
            </label>
            <textarea
              {...register('description')}
              rows={3}
              placeholder="Notas adicionales..."
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={createExpenseMutation.isPending || isLoadingCategories}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
        >
          {createExpenseMutation.isPending ? 'Guardando...' : 'Agregar gasto'}
        </button>
      </form>
    </div>
  );
}
