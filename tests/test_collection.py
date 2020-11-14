from unittest import mock

import grpc
import pytest
from grpc._channel import _UnaryUnaryMultiCallable as Uum

from milvus import DataType, BaseError

from factorys import collection_name_factory

from utils import MockGrpcError


class TestCreateCollection:
    def test_create_collection_normal(self, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ]
        }

        try:
            connect.create_collection(collection_name, collection_param)
        except Exception as e:
            pytest.fail("Unexpected MyError: ".format(str(e)))
        finally:
            connect.drop_collection(collection_name)

    def test_create_collection_repeat(self, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ]
        }

        try:
            connect.create_collection(collection_name, collection_param)
            with pytest.raises(BaseError):
                connect.create_collection(collection_name, collection_param)
        except Exception as e:
            pytest.fail("Unexpected MyError: ".format(str(e)))
        finally:
            connect.drop_collection(collection_name)

    @pytest.mark.parametrize("sd", [DataType.INT32, DataType.INT64, DataType.BOOL, DataType.FLOAT, DataType.DOUBLE])
    @pytest.mark.parametrize("vd", [DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR])
    def test_create_collection_scalar_vector(self, sd, vd, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "A", "type": sd},
                {"name": "v", "type": vd, "params": {"dim": 128}}
            ]
        }

        try:
            connect.create_collection(collection_name, collection_param)
        except Exception as e:
            pytest.fail("Unexpected MyError: ".format(str(e)))
        finally:
            connect.drop_collection(collection_name)

    def test_create_collection_segment_row_limit(self, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ],
            "segment_row_limit": 10000
        }

        try:
            connect.create_collection(collection_name, collection_param)
        except Exception as e:
            pytest.fail("Unexpected MyError: ".format(str(e)))
        finally:
            connect.drop_collection(collection_name)

    @pytest.mark.parametrize("srl", [1, 10000000])
    def test_create_collection_segment_row_limit_outrange(self, srl, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ],
            "segment_row_limit": srl
        }

        with pytest.raises(BaseError):
            connect.create_collection(collection_name, collection_param)

    @pytest.mark.parametrize("srl", [None, "123"])
    def test_create_collection_segment_row_limit_invalid(self, srl, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ],
            "segment_row_limit": srl
        }

        with pytest.raises(BaseError):
            connect.create_collection(collection_name, collection_param)

    @pytest.mark.parametrize("autoid", [True, False])
    def test_create_collection_segment_row_limit_outrange(self, autoid, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ],
            "segment_row_limit": 10000,
            "auto_id": autoid
        }

        try:
            connect.create_collection(collection_name, collection_param)
        except Exception as e:
            pytest.fail("Unexpected MyError: ".format(str(e)))
        finally:
            connect.drop_collection(collection_name)

    def test_create_collection_exception(self, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ],
            "segment_row_limit": 10000,
            "auto_id": False
        }

        mock_grpc_timeout = mock.MagicMock(side_effect=grpc.FutureTimeoutError())
        with mock.patch.object(Uum, 'future', mock_grpc_timeout):
            with pytest.raises(grpc.FutureTimeoutError):
                connect.create_collection(collection_name, collection_param)

        mock_grpc_error = mock.MagicMock(side_effect=MockGrpcError())
        with mock.patch.object(Uum, 'future', mock_grpc_error):
            with pytest.raises(grpc.RpcError):
                connect.create_collection(collection_name, collection_param)

        mock_exception = mock.MagicMock(side_effect=Exception("error"))
        with mock.patch.object(Uum, 'future', mock_exception):
            with pytest.raises(Exception):
                connect.create_collection(collection_name, collection_param)


class TestListCollections:
    def test_list_collections_normal(self, connect, vcollection):
        collections = connect.list_collections()
        assert isinstance(collections, list)
        assert len(collections) == 1
        assert collections[0] == vcollection


class TestGetCollectionInfo:
    def test_get_collection_info_normal(self, connect, ivrecords):
        info = connect.get_collection_info(ivrecords)

        assert info['auto_id'] is True
        for f in info['fields']:
            assert f['name'] in ('Vec', 'Int')
        assert info['segment_row_limit'] == 100000


class TestGetCollectionStats:
    def test_get_collection_stats_normal(self, connect, ivrecords):
        stats = connect.get_collection_stats(ivrecords)
        assert stats["partition_count"] == 1
        assert stats["row_count"] == 10000
        assert stats["partitions"][0]["row_count"] == 10000
        assert stats["partitions"][0]["segment_count"] == 1


class TestDropCollection:
    def test_drop_collection_normal(self, connect):
        collection_name = collection_name_factory()
        collection_param = {
            "fields": [
                {"name": "v", "type": DataType.FLOAT_VECTOR, "params": {"dim": 128}}
            ]
        }

        try:
            connect.create_collection(collection_name, collection_param)
        except Exception as e:
            connect.drop_collection(collection_name)
            pytest.fail("Unexpected create collection Error: ".format(str(e)))

        connect.drop_collection(collection_name)

    def test_drop_collection_with_nonexist_collection(self, connect):
        with pytest.raises(BaseError):
            connect.drop_collection("test_xxxxxxxxx")
