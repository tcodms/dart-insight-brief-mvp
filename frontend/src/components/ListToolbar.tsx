import { Search } from 'lucide-react'

export type ListOrder = 'newest' | 'oldest' | 'name'

export function sortList<T>(items: T[], order: ListOrder, name: (item: T) => string, date: (item: T) => string) {
  return [...items].sort((a, b) => {
    if (order === 'name') return name(a).localeCompare(name(b), 'ko') || date(b).localeCompare(date(a))
    return order === 'oldest' ? date(a).localeCompare(date(b)) : date(b).localeCompare(date(a))
  })
}

export default function ListToolbar({ query, onSearch, order, onOrder, placeholder, summary, nameLabel }: {
  query: string; onSearch: (query: string) => void;
  order: ListOrder; onOrder: (order: ListOrder) => void;
  placeholder: string; summary: string; nameLabel: string;
}) {
  return <div className="list-toolbar">
    <span className="list-summary" aria-live="polite">{summary}</span>
    <div className="list-controls">
      <label className="catalog-search">
        <span className="sr-only">{placeholder}</span>
        <Search size={16} aria-hidden="true" />
        <input type="search" value={query} onChange={(event) => onSearch(event.target.value)} placeholder={placeholder} />
      </label>
      <select aria-label="정렬 기준" value={order} onChange={(event) => onOrder(event.target.value as ListOrder)}>
        <option value="newest">최신순</option>
        <option value="oldest">오래된순</option>
        <option value="name">{nameLabel} 가나다순</option>
      </select>
    </div>
  </div>
}
