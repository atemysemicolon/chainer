import six

from chainer import variable


class Updater(object):

    """Base class of updater callbacks.

    Updater is a callable object that updates the optimizer. It is usually set
    to a :class:`Trainer` object, and called for each minibatch given by the
    training dataset.

    Trainer object gives two arguments to an updater: an input minibatch and
    the optimizer. The given optimizer should be used, since the trainer
    watches its iteration counter :attr:`~Optimizer.t` to decide when to invoke
    extensions. An updater still can hold other optimizers as well to implement
    an algorithm that involves multiple optimization problems.

    An updater must returns a `result dictionary`. It is a dictionary with
    string keys and numeric values. The result dictionary is stored to
    ``trainer.result['training']``, and used by some extensions to compute
    statistics of the training result (e.g. mean loss value over an expoch).

    If an updater supports serialization, then the trainer serializes the
    updater in its own serialization definition. In the case that the updater
    holds its own optimizers as described above, do not forget to serialize
    them.

    Typical updater just passes a loss function to the optimizer with the input
    minibatch as the arguments. Such an implementation is given by the
    :class:`StandardUpdater` class.

    .. note::
       You can also write your updater as a plain function with appropriate
       interface.

    """
    def __call__(self, inputs, optimizer):
        """Updates the optimizer.

        Implementations should override this operator. It updates the optimizer
        with a given input minibatch.

        Args:
            inputs: Input minibatch. This is just a value generated by the
                batch iterator of the training dataset. See
                :meth:`Dataset.get_batch_iterator` for its content.
            optimizer (Optimizer): Optimizer of the trainer.

        Returns:
            dict: Result dictionary with string keys and numeric values.

        """
        raise NotImplementedError

    def serialize(self, serializer):
        pass


class StandardUpdater(Updater):

    """Standard implementation of Updater.

    This is a typical implementation of the :class:`Updater` interface. It
    wraps the input arrays by :class:`Variable` objects, and calls the
    optimzier with a given loss function. The variables are also passed to the
    optimizer as arguments of the loss function.

    This updater automatically builds a result dictionary for each update. It
    scans the ``__dict__`` attribute of the target link and finds all
    attributes which are variables of size-1 arrays. Then, it adds them to the
    result dictionary. Note that it does not scan the descendant links of the
    target link.

    """
    def __init__(self, lossfun=None):
        self._lossfun = lossfun

    def __call__(self, inputs, optimizer):
        if not isinstance(inputs, tuple):
            inputs = inputs,
        in_vars = [variable.Variable(a) for a in inputs]
        lossfun = optimizer.target if self._lossfun is None else self._lossfun
        optimizer.update(lossfun, *in_vars)

        result = {}
        for name, value in six.iteritems(optimizer.target.__dict__):
            if isinstance(value, variable.Variable):
                x = value.data
                if x.size == 1:
                    result[name] = x
        return result