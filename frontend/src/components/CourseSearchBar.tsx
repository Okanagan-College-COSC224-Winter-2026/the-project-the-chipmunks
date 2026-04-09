import './CourseSearchBar.css';

interface Props {
  query: string;
  onQueryChange: (q: string) => void;
  resultCount: number;
}

export default function CourseSearchBar({ query, onQueryChange, resultCount }: Props) {
  return (
    <div className='CourseSearchBar'>
      <input
        type='text'
        className='CourseSearchBar__input'
        placeholder='Search courses...'
        value={query}
        onChange={e => onQueryChange(e.target.value)}
      />
      {query && (
        <span className='CourseSearchBar__count'>
          {resultCount} result{resultCount !== 1 ? 's' : ''}
        </span>
      )}
      {query && (
        <button
          className='CourseSearchBar__clear'
          onClick={() => onQueryChange('')}
        >
          Clear
        </button>
      )}
    </div>
  );
}
