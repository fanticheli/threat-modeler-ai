# Design System

Guia de design e componentes visuais do Threat Modeler AI.

## Cores

### Cores Principais

| Nome | Hex | Uso |
|------|-----|-----|
| Primary | `#2563eb` | Botões, links, destaques |
| Primary Dark | `#1d4ed8` | Hover states |
| Success | `#22c55e` | Alertas positivos, baixa severidade |
| Warning | `#eab308` | Alertas, média severidade |
| Danger | `#ef4444` | Erros, alta severidade |
| Critical | `#dc2626` | Severidade crítica |

### Cores de Severidade

| Severidade | Cor | Classe Tailwind |
|------------|-----|-----------------|
| Critical | Vermelho escuro | `bg-red-600` |
| High | Laranja | `bg-orange-500` |
| Medium | Amarelo | `bg-yellow-500` |
| Low | Verde | `bg-green-500` |

### Cores Neutras

| Nome | Hex | Uso |
|------|-----|-----|
| Gray 50 | `#f9fafb` | Backgrounds |
| Gray 100 | `#f3f4f6` | Cards |
| Gray 500 | `#6b7280` | Texto secundário |
| Gray 800 | `#1f2937` | Texto principal |

## Tipografia

**Font Family:** System fonts (Tailwind default)

| Elemento | Classe | Uso |
|----------|--------|-----|
| H1 | `text-2xl font-bold` | Títulos de página |
| H2 | `text-xl font-semibold` | Seções |
| H3 | `text-lg font-medium` | Subseções |
| Body | `text-base` | Texto padrão |
| Small | `text-sm` | Labels, hints |
| XSmall | `text-xs` | Badges, metadata |

## Componentes

### Botões

```jsx
// Primário
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
  Analisar
</button>

// Secundário
<button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
  Cancelar
</button>

// Danger
<button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
  Excluir
</button>
```

### Cards

```jsx
<div className="bg-white rounded-xl shadow-lg p-6">
  {/* Conteúdo */}
</div>
```

### Badges de Severidade

```jsx
// Critical
<span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
  Critical
</span>

// High
<span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-medium">
  High
</span>

// Medium
<span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
  Medium
</span>

// Low
<span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
  Low
</span>
```

### Alertas

```jsx
// Erro
<div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
  Mensagem de erro
</div>

// Sucesso
<div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
  Mensagem de sucesso
</div>
```

## Ícones

Usamos emojis como ícones para simplicidade:

| Ícone | Uso |
|-------|-----|
| 🛡️ | Logo/Segurança |
| 📁 | Upload |
| ⚠️ | Warning |
| ✅ | Sucesso |
| ❌ | Erro |
| 🔴 | Critical |
| 🟠 | High |
| 🟡 | Medium |
| 🟢 | Low |

## Espaçamento

Baseado em múltiplos de 4px (Tailwind default):

| Classe | Valor |
|--------|-------|
| `p-2` | 8px |
| `p-4` | 16px |
| `p-6` | 24px |
| `p-8` | 32px |
| `gap-2` | 8px |
| `gap-4` | 16px |

## Responsividade

Breakpoints (Tailwind default):

| Breakpoint | Min Width |
|------------|-----------|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |
