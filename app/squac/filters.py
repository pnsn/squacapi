"""Common methods for filtering classes to share"""


def in_sql(queryset, name, value):
    """perform generic 'in' SQL statement exp

    select * from networks where code in ('uw', 'uo');
    """
    # this just builds a networks__in
    if name is not None:
        values = value.split(",")
        name_in = '__'.join([name, 'in'])
        queryset = queryset.filter(**{name_in: values})
    return queryset


def regex_sql(queryset, name, value):
    """perform python regex searches on field

        select * from  networks where code like %RC%;
        turn * into .
    """

    if name is not None:
        value = value.replace('*', '.')
        name_regex = '__'.join([name, 'iregex'])
        queryset = queryset.filter(**{name_regex: value})
    return queryset
