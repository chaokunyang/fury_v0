import { GenericReader, GenericWriter, InternalSerializerType, RefFlags, Serializer } from "../type";
import { Fury } from "../type";
import stringSerializer from "../internalSerializer/string";
import boolSerializer from "../internalSerializer/bool";
import { int8Serializer, int32Serializer, int64Serializer, floatSerializer, doubleSerializer } from "../internalSerializer/number";


const buildTypedArray = <T>(fury: Fury, reader: GenericReader, writer: GenericWriter) => {
    const serializer = arraySerializer(fury);
    return {
        read: (shouldSetRef: boolean) => {
            return serializer.read(shouldSetRef, [reader])
        },
        write: (v: T[]) => {
            return serializer.write(v, [writer])
        }
    } as Serializer<T[]>
}

export const stringArraySerializer = (fury: Fury) => {
    const { readBySerializerWithOutTypeId, classResolver } = fury;
    const { read } = classResolver.getSerializerById(InternalSerializerType.STRING);
    const { writeWithOutType } = stringSerializer(fury);
    return buildTypedArray<string>(
        fury,
        () => readBySerializerWithOutTypeId(read),
        writeWithOutType,
    )
};

export const boolArraySerializer = (fury: Fury) => {
    const { read } = boolSerializer(fury);
    const { binaryWriter } = fury;
    const { writeUInt8 } = binaryWriter;

    return buildTypedArray<boolean>(
        fury,
        read,
        (v: boolean) => {
            writeUInt8(v ? 1 : 0)
        },
    )
};


export const shortArraySerializer = (fury: Fury) => {
    const { read } = int8Serializer(fury);
    const { binaryWriter } = fury;
    const { writeInt8 } = binaryWriter;
    return buildTypedArray<number>(
        fury,
        read,
        writeInt8,
    )
};

export const intArraySerializer = (fury: Fury) => {
    const { read } = int32Serializer(fury);
    const { binaryWriter } = fury;
    const { writeInt32 } = binaryWriter;

    return buildTypedArray<number>(
        fury,
        read,
        writeInt32,
    )
};
export const longArraySerializer = (fury: Fury) => {
    const { read } = int64Serializer(fury);
    const { binaryWriter } = fury;
    const { writeInt64 } = binaryWriter;

    return buildTypedArray<number>(
        fury,
        read,
        writeInt64,
    )
};
export const floatArraySerializer = (fury: Fury) => {
    const { read } = floatSerializer(fury);
    const { binaryWriter } = fury;
    const { writeFloat } = binaryWriter;

    return buildTypedArray<number>(
        fury,
        read,
        writeFloat,
    )
};
export const doubleArraySerializer = (fury: Fury) => {
    const { read } = doubleSerializer(fury);
    const { binaryWriter } = fury;
    const { writeDouble } = binaryWriter;


    return buildTypedArray<number>(
        fury,
        read,
        writeDouble,
    )
};


export const arraySerializer = (fury: Fury) => {
    const { binaryView, binaryWriter, read, referenceResolver, writeNullOrRef, write } = fury;
    const { pushReadObject, pushWriteObject } = referenceResolver;
    const { writeInt8, writeInt16, writeInt32 } = binaryWriter;
    const { readInt32 } = binaryView;
    return {
        read: (shouldSetRef: boolean, genericReaders?: GenericReader[]) => {
            const len = readInt32();
            const result = new Array(len);
            if (shouldSetRef) {
                pushReadObject(result);
            }
            // if the array hash concrete type, we can use the genericReader, otherwise use the normal read
            let itemReader: GenericReader | null = null;
            if (genericReaders) {
                itemReader = genericReaders[0];
            }
            if (itemReader) {
                for (let index = 0; index < len; index++) {
                    result[index] = itemReader();
                }
            } else {
                for (let index = 0; index < len; index++) {
                    result[index] = read();
                }
            }
            return result;
        },
        write: (v: any[], genericWriters?: GenericWriter[]) => {
            if (writeNullOrRef(v)) {
                return;
            }
            writeInt8(RefFlags.RefValueFlag);
            writeInt16(InternalSerializerType.ARRAY);
            pushWriteObject(v);
            writeInt32(v.length);
            // if the array hash concrete type, we can use the genericWriter, otherwise use the normal writer
            let itemWriter: Serializer['write'] | null = null;
            if (genericWriters) {
                itemWriter = genericWriters[0];
            }
            if (itemWriter) {
                v.forEach(x => {
                    itemWriter!(x);
                })
            } else {
                v.forEach(x => {
                    write(x);
                })
            }
        }
    }
}
