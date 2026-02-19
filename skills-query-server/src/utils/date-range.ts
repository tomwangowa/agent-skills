export interface DateRange {
  since: Date;
  until: Date;
}

export function parseDateRange(range: string): DateRange {
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 86400000 - 1);

  switch (range) {
    case 'today':
      return { since: startOfDay, until: endOfDay };

    case 'yesterday': {
      const yesterday = new Date(startOfDay.getTime() - 86400000);
      return { since: yesterday, until: startOfDay };
    }

    case 'this-week': {
      const day = now.getDay();
      const diff = day === 0 ? 6 : day - 1; // Monday = start
      const monday = new Date(startOfDay.getTime() - diff * 86400000);
      return { since: monday, until: endOfDay };
    }

    case 'last-week': {
      const day = now.getDay();
      const diff = day === 0 ? 6 : day - 1;
      const thisMonday = new Date(startOfDay.getTime() - diff * 86400000);
      const lastMonday = new Date(thisMonday.getTime() - 7 * 86400000);
      return { since: lastMonday, until: thisMonday };
    }

    case 'this-month': {
      const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      return { since: firstOfMonth, until: endOfDay };
    }

    case 'all':
      return { since: new Date(0), until: endOfDay };

    default:
      throw new Error(`Unknown date range: "${range}". Use: today, yesterday, this-week, last-week, this-month, all`);
  }
}
