# 定义带参数的装饰器
def custom_decorator(parameter1, parameter2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"Decorator received parameters: {parameter1}, {parameter2}")
            result = func(parameter1, parameter2, *args, **kwargs)
            return result
        return wrapper
    return decorator

# 使用装饰器并传递参数给装饰器
@custom_decorator("Hello", 42)
def my_function(param1, param2, *args, **kwargs):
    print(f"Function is called with parameters: {param1}, {param2}, {args}, {kwargs}.")

# 调用被修饰的函数
my_function("World", 84, "Extra Arg 1", extra_arg="Extra Arg 2")
