import normalize.coll
import normalize.exc as exc
import normalize.record


def record_id(object_, type_=None):
    """Implementation of id() which is overridable and knows about record's
    primary_key property.  Returns if the two objects may be the "same";
    returns None for other types, meaning all bets about identity are off.

    Curiously, this function resembles conversion between a "record" and a
    "tuple": stripping the logical names from the atomic values.
    """
    if type_ is None:
        type_ = type(object_)

    key_vals = list()
    if not type_.primary_key and issubclass(
        type_, normalize.coll.Collection
    ):
        # FIXME: unordered collections will rarely match each other
        gen = (
            object_.itertuples() if hasattr(object_, "itertuples") else
            type_.coll_to_tuples(object_)
        )
        return tuple(
            record_id(v, type_.itemtype) for k, v in gen
        )

    for prop in type_.primary_key or type_._sorted_properties:
        val = getattr(object_, prop.name, None)
        if val is not None and prop.valuetype:
            value_type_list = (
                prop.valuetype if isinstance(prop.valuetype, tuple) else
                (prop.valuetype,)
            )
            val_pk = ()
            set_elements = 0
            for value_type in value_type_list:
                if issubclass(value_type, normalize.record.Record):
                    pk = record_id(val, value_type)
                    pk_elements = len([x for x in pk if x is not None])
                    if not val_pk or pk_elements > set_elements:
                        val_pk = pk
                        set_elements = pk_elements

            val_pk = val_pk or val
            try:
                val_pk.__hash__()
            except TypeError:
                raise exc.KeyHashError(
                    prop=str(prop),
                    typename=type_.__name__,
                )
            key_vals.append(val_pk)
        else:
            key_vals.append(val)

    return tuple(key_vals)