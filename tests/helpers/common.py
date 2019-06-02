
        
def related(instance, field_name):
    '''
    Returns related object/list of related objects for rel field FIELD_NAME.
    Raises exception if field FIELD_NAME is not rel.
    '''
    field = instance.model.field(field_name)
    if not field.rel:
        raise Exception('related(instance, field_name) might be called only for rel fields'.
                        format(type(instance)))
    instances = instance.get_val(field).inst()
    if field.multi:
        return instances
    else:
        if instances:
            return instances[0]
        else:
            return None

